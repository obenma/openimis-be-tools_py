import io
import json
from datetime import date
from unittest.mock import patch, PropertyMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory

from claim.models import Claim
from core.test_helpers import create_test_interactive_user, create_test_claim_admin
from insuree.test_helpers import create_test_insuree
from location.test_helpers import create_test_health_facility
from medical.test_helpers import create_test_diagnosis, create_test_item
from tools import utils, views
from tools.services import upload_claim, InvalidXMLError


def claim_xml(hf, admin, insuree, diagnosis, item, code="UPL0001", chf_id=None):
    today = date.today().strftime("%d/%m/%Y")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Claim>
  <Details>
    <ClaimDate>{today}</ClaimDate>
    <HFCode>{hf.code}</HFCode>
    <ClaimAdmin>{admin.code}</ClaimAdmin>
    <ClaimCode>{code}</ClaimCode>
    <CHFID>{chf_id or insuree.chf_id}</CHFID>
    <StartDate>{today}</StartDate>
    <EndDate>{today}</EndDate>
    <ICDCode>{diagnosis.code}</ICDCode>
    <Comment>uploaded</Comment>
    <Total>30</Total>
    <VisitType>O</VisitType>
  </Details>
  <Items>
    <Item><ItemCode>{item.code}</ItemCode><ItemPrice>10</ItemPrice><ItemQuantity>3</ItemQuantity></Item>
  </Items>
  <Services></Services>
</Claim>""".encode()


@patch("tools.services.settings.ROW_SECURITY", new_callable=PropertyMock, return_value=True)
class ClaimUploadTest(TestCase):
    """OP-3246: a claim XML upload enters the claim through the ORM (no stored procedure)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_interactive_user(username="test_claim_upload_user")
        cls.hf = create_test_health_facility(code="UPLHF01")
        cls.admin = create_test_claim_admin(custom_props={"code": "UPLCA01", "health_facility_id": cls.hf.id})
        cls.insuree = create_test_insuree(custom_props={"chf_id": "880000001"})
        cls.diagnosis = create_test_diagnosis(custom_props={"code": "UPLD1"})
        cls.item = create_test_item("D", custom_props={"code": "UPLI1"})

    def _upload(self, xml):
        # Same parsing as the view: a document whose root element is <Claim>.
        return upload_claim(self.user, utils.sanitize_xml(io.BytesIO(xml)))

    def _xml(self, **kwargs):
        return claim_xml(self.hf, self.admin, self.insuree, self.diagnosis, self.item, **kwargs)

    def test_upload_enters_the_claim_with_its_items(self, _row_security):
        self._upload(self._xml())
        claim = Claim.objects.get(code="UPL0001", validity_to__isnull=True)
        self.assertEqual(claim.status, Claim.STATUS_ENTERED)
        self.assertEqual(claim.health_facility_id, self.hf.id)
        self.assertEqual(claim.admin_id, self.admin.id)
        self.assertEqual(claim.insuree_id, self.insuree.id)
        self.assertEqual(claim.icd_id, self.diagnosis.id)
        self.assertEqual(claim.visit_type, "O")
        self.assertEqual(claim.explanation, "uploaded")
        items = list(claim.items.filter(validity_to__isnull=True))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].item_id, self.item.id)
        self.assertEqual(int(items[0].qty_provided), 3)
        self.assertEqual(int(items[0].price_asked), 10)
        self.assertEqual(int(claim.claimed), 30)

    def test_upload_refuses_an_unknown_insuree(self, _row_security):
        with self.assertRaises(InvalidXMLError) as cm:
            self._upload(self._xml(code="UPL0002", chf_id="999999999"))
        self.assertEqual("Unknown insuree number", str(cm.exception))

    def test_upload_refuses_a_duplicated_claim_code(self, _row_security):
        self._upload(self._xml(code="UPL0003"))
        with self.assertRaises(InvalidXMLError) as cm:
            self._upload(self._xml(code="UPL0003"))
        self.assertEqual("Duplicated claim code", str(cm.exception))

    def test_view_answers_malformed_xml_with_a_json_error(self, _row_security):
        request = RequestFactory().post(
            "/api/tools/extracts/upload_claims",
            {"bad.xml": SimpleUploadedFile("bad.xml", b"<Claim><Details>", content_type="text/xml")},
        )
        request.user = self.user
        response = views.upload_claims(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content),
                         {"success": False, "errors": ["File 'bad.xml' is not a valid XML"]})
