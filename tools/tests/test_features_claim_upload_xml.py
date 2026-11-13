"""
Tests for the @backend scenarios of features/claim-upload-xml.feature.

The claim XML is imported through tools.services.upload_claim, which calls the
uspUpdateClaimFromPhone procedure (PostgreSQL function on the CSU databases).
Row security is patched off for the upload so that the procedure itself is tested;
the health facility check of row security is covered in test_claims.py.
"""
import io
import random
import unittest
from datetime import date, timedelta
from unittest.mock import patch, PropertyMock
from xml.etree import ElementTree

import pyzipper
from django.db import connection
from django.test import TestCase

from claim.models import Claim
from claim.test_helpers import create_test_claim_admin
from core.test_helpers import create_test_interactive_user
from insuree.test_helpers import create_test_insuree
from location.test_helpers import create_test_health_facility, create_test_location
from medical.models import Diagnosis
from medical.test_helpers import create_test_diagnosis, create_test_service
from program.test_helpers import create_test_program
from tools.services import InvalidXMLError, open_claim_archive, upload_claim


def _diagnosis():
    # The ICD sequence of the kept test DB can lag behind the seeded rows; reuse a seeded code.
    diag = Diagnosis.objects.filter(validity_to__isnull=True).extra(
        where=['LENGTH("ICDCode") <= 6']).first()
    return diag or create_test_diagnosis()


def _claim_xml(hf_code, claim_admin_code, claim_code, chf_id, icd_code, program,
               service_code=None, item_code=None, end_date="2024-06-03", pregnancy_age=None):
    items = f"""<Items><Item><ItemCode>{item_code}</ItemCode><ItemQuantity>1</ItemQuantity>
                <ItemPrice>1000.00</ItemPrice></Item></Items>""" if item_code else ""
    services = f"""<Services><Service><ServiceCode>{service_code}</ServiceCode>
                <ServiceQuantity>1</ServiceQuantity><ServicePrice>2000.00</ServicePrice></Service></Services>""" \
        if service_code else ""
    preg = f"<PregnancyAge>{pregnancy_age}</PregnancyAge>" if pregnancy_age is not None else ""
    return ElementTree.fromstring(f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Claim>
            <Details>
                <ClaimDate>2024-06-04</ClaimDate>
                <HFCode>{hf_code}</HFCode>
                <ClaimAdmin>{claim_admin_code}</ClaimAdmin>
                <ClaimCode>{claim_code}</ClaimCode>
                <Program>{program}</Program>
                <CHFID>{chf_id}</CHFID>
                <StartDate>2024-06-03</StartDate>
                <EndDate>{end_date}</EndDate>
                <ICDCode>{icd_code}</ICDCode>
                <VisitType>O</VisitType>
                {preg}
            </Details>
            {items}
            {services}
        </Claim>""".encode("utf-8"))


class _ClaimUploadBase(TestCase):
    PROGRAM_NAME = "SPXU HIV"

    @classmethod
    def setUpTestData(cls):
        cls.program = create_test_program(code="SPXUHIV", name=cls.PROGRAM_NAME)
        location = create_test_location('D')
        cls.hf = create_test_health_facility('SPXUHF', location.id)
        cls.insuree = create_test_insuree()
        cls.service = create_test_service("A")
        cls.diagnosis = _diagnosis()
        cls.claim_admin = create_test_claim_admin(
            {"code": "SPXUCA", "health_facility_id": cls.hf.id})

    def setUp(self):
        patcher = patch('tools.services.settings.ROW_SECURITY', new_callable=PropertyMock)
        self.addCleanup(patcher.stop)
        patcher.start().return_value = False
        self.user = create_test_interactive_user(username="SPXUClaimUploader")

    def xml(self, claim_code=None, program=None, **kwargs):
        return _claim_xml(
            self.hf.code, self.claim_admin.code,
            claim_code or f"SPXU{random.randint(1, 999999)}",
            self.insuree.chf_id, self.diagnosis.code,
            program if program is not None else self.PROGRAM_NAME,
            service_code=kwargs.pop("service_code", self.service.code),
            # no item by default: on the test DBs "tblClaimItems"."ClaimItemStatus" has no DEFAULT and the
            # procedure does not set it (see report); the scenarios only need a service
            item_code=kwargs.pop("item_code", None),
            **kwargs,
        )

    def imported(self, claim_code):
        return Claim.objects.get(code=claim_code, health_facility_id=self.hf.id, validity_to__isnull=True)


class ClaimUploadPostgresTest(_ClaimUploadBase):
    # Scenario: A claim XML is imported on PostgreSQL (@redmine-34740 @redmine-34919 @redmine-36409 @redmine-36410)
    def test_claim_xml_is_imported_on_postgresql(self):
        self.assertEqual(connection.vendor, "postgresql")
        with connection.cursor() as cur:
            cur.execute("""SELECT 1 FROM pg_proc WHERE proname = 'uspUpdateClaimFromPhone'""")
            self.assertIsNotNone(cur.fetchone(), "uspUpdateClaimFromPhone function missing")

        self.assertTrue(upload_claim(self.user, self.xml(claim_code="SPXUPG1")))

        claim = self.imported("SPXUPG1")
        self.assertEqual(claim.status, Claim.STATUS_ENTERED)
        self.assertEqual(claim.insuree_id, self.insuree.id)
        self.assertEqual(claim.icd_id, self.diagnosis.id)
        self.assertEqual(claim.services.filter(validity_to__isnull=True).count(), 1)
        self.assertEqual(float(claim.claimed), 2000.0)

    # Scenario: The import checks the programme (@redmine-34368) - known programme
    def test_known_programme_is_stored(self):
        self.assertTrue(upload_claim(self.user, self.xml(claim_code="SPXUPRG1")))
        self.assertEqual(self.imported("SPXUPRG1").program_id, self.program.pk)

    # Scenario: The import checks the programme (@redmine-34368) - unknown programme
    def test_unknown_programme_fails(self):
        with self.assertRaises(InvalidXMLError) as cm:
            upload_claim(self.user, self.xml(claim_code="SPXUPRG2", program="NOSUCHPROG"))
        self.assertEqual(str(cm.exception), "Unknown program")
        self.assertFalse(Claim.objects.filter(code="SPXUPRG2").exists())

    # Scenario: Importing a claim code twice fails (@redmine-36945)
    def test_importing_claim_code_twice_fails(self):
        self.assertTrue(upload_claim(self.user, self.xml(claim_code="SPXUDUP")))
        with self.assertRaises(InvalidXMLError) as cm:
            upload_claim(self.user, self.xml(claim_code="SPXUDUP"))
        self.assertEqual(str(cm.exception), "Duplicated claim code")
        self.assertEqual(Claim.objects.filter(code="SPXUDUP", validity_to__isnull=True).count(), 1)


class ImportedClaimWorkflowTest(_ClaimUploadBase):
    # Scenario: An imported claim has its mandatory feedback flag and source (@redmine-34664 @redmine-36408)
    def test_imported_claim_has_feedback_flag_and_source(self):
        from claim.services import submit_claim

        self.assertTrue(upload_claim(self.user, self.xml(claim_code="SPXUFB1")))
        claim = self.imported("SPXUFB1")

        self.assertIs(claim.feedback_available, False)
        self.assertIsNone(claim.feedback_id)
        self.assertIsNone(claim.feedback)  # no "Feedback matching query does not exist"
        self.assertEqual(claim.source, Claim.SOURCE_XML)

        # the mandatory-fields validation that raised the ValidationError on live
        try:
            claim.full_clean(validate_unique=False)
        except Exception as exc:  # other fields may be reported, never the feedback
            self.assertNotIn("Feedback matching query does not exist", str(exc))

        with patch('claim.services.settings.ROW_SECURITY', False):
            submit_claim(claim, self.user)
        claim.refresh_from_db()
        self.assertIn(claim.status, (Claim.STATUS_CHECKED, Claim.STATUS_REJECTED))

    # Scenario: The pregnancy age is set on an imported Chèque Santé claim (@redmine-36240 @redmine-37189 @redmine-37567)
    @unittest.skip("not validated: #36240 - the pregnancy age computation of uspUpdateClaimFromPhone "
                   "is only on origin/feature-36240 (tools 1e153dc), not merged into dev-csu/test-csu")
    def test_pregnancy_age_is_computed_on_cheque_sante_claim(self):
        from policy.test_helpers import create_test_policy
        from product.test_helpers import create_test_product

        product = create_test_product("SPXUCCS")  # attached to the CCS programme
        ccs = product.program
        start = date(2024, 5, 6)  # a Monday
        create_test_policy(product, self.insuree, custom_props={
            "start_date": start, "effective_date": start, "enroll_date": start, "pregnancy_age": 10})
        end = start + timedelta(weeks=4)

        self.assertTrue(upload_claim(self.user, self.xml(
            claim_code="SPXUPREG", program=ccs.nameProgram, end_date=end.isoformat())))
        self.assertEqual(self.imported("SPXUPREG").pregnancy_age, 14)


class ClaimArchiveLayoutTest(TestCase):
    PASSWORD = "spxu-test-pwd"

    def _zip(self, members):
        buf = io.BytesIO()
        with pyzipper.AESZipFile(buf, 'w', compression=pyzipper.ZIP_DEFLATED,
                                 encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(self.PASSWORD.encode())
            for name in members:
                zf.writestr(name, b"<Claim><Details><ClaimCode>%s</ClaimCode></Details></Claim>" % name.encode())
        buf.seek(0)
        return buf

    def _read(self, archive):
        claims = open_claim_archive(archive, self.PASSWORD)
        names = []
        for name, f in claims:
            with f:
                ElementTree.fromstring(f.read())
            names.append(name)
        return names

    # Scenario: An archive with one claim imports - single XML file at the archive root (@redmine-36904)
    def test_single_xml_at_root(self):
        self.assertEqual(self._read(self._zip(["claim_1.xml"])), ["claim_1.xml"])

    # Scenario: An archive with one claim imports - two XML files inside a folder (@redmine-36904)
    def test_two_xml_inside_folder(self):
        names = self._read(self._zip(["Claims/claim_1.xml", "Claims/claim_2.xml"]))
        self.assertEqual(sorted(names), ["Claims/claim_1.xml", "Claims/claim_2.xml"])
