"""
Tests for backend/features/insuree-enquiry.feature, tools module part (XML enrolment upload).
"""
from django.test import TestCase

from insuree.test_helpers import create_test_insuree
from tools.services import get_or_create_insuree_from_xml


class XmlEnrolmentChfidTest(TestCase):
    # Scenario: The XML enrolment upload trims the CHFID (@redmine-38348)
    def test_xml_upload_trims_chfid(self):
        head = create_test_insuree()
        xml = {
            "CHFID": "120902348063481 ",
            "LastName": "XML", "OtherNames": "Feature", "DOB": "1990-01-01", "Gender": "F",
            "isHead": False, "CardIssued": False, "isOffline": False,
            "CurVillage": head.current_village_id,
        }
        insuree, _ = get_or_create_insuree_from_xml(xml, -1, family_id=head.family_id)
        self.assertEqual(insuree.chf_id, "120902348063481",
                         "XML CHFID normalisation (#38348, tools PR 43) is not in this checkout")
