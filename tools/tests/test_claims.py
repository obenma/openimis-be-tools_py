from unittest.mock import patch, PropertyMock

from django.test import TestCase
from unittest import mock

from tools.services import upload_claim, InvalidXMLError, get_xml_element, get_xml_element_int, \
    InvalidXmlInt, create_officer_feedbacks_export, create_officer_renewals_export
from xml.etree import ElementTree
from datetime import date, timedelta

from core.test_helpers import create_test_officer, create_test_interactive_user

from policy.services import insert_renewals
from claim.models import Claim
from claim.services import create_feedback_prompt
from claim.test_helpers import (
    create_test_claim,
)


class UploadClaimsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = create_test_interactive_user(username="test_upload_claim_user")

    def test_upload_claims_unknown_hf(self):
        # Mock users fail build_user_location_filter_query's isinstance check and fall through to legacy T-SQL, hanging the DB connection.
        with patch('tools.services.settings.ROW_SECURITY', new_callable=PropertyMock) as row_security_mock:
            row_security_mock.return_value = True
            with self.assertRaises(InvalidXMLError) as cm:
                upload_claim(
                    self.test_user,
                    ElementTree.fromstring(
                        """
                            <root>
                                <Claim>
                                    <Details>
                                        <HFCode>WRONG</HFCode>
                                    </Details>
                                </Claim>
                            </root>
                        """
                    ),
                )
            self.assertEqual(
                "User cannot upload claims for health facility WRONG",
                str(cm.exception),
            )


class GetXmlElement(TestCase):
    def test_get_xml_element(self):
        test_xml = ElementTree.fromstring(
            """
                <root>
                    <Exists>Exists</Exists>
                    <Int>123</Int>
                    <NotInt>123x</NotInt>
                    <Float>123.10</Float>
                    <NotFloat>123$10</NotFloat>
                </root>
            """
        )
        self.assertEqual("Exists", get_xml_element(test_xml, "Exists"))
        with self.assertRaises(AttributeError):
            get_xml_element(test_xml, "NotExists")
        self.assertEqual("DefaultValue", get_xml_element(test_xml, "NotExists", "DefaultValue"))

        self.assertEqual(123, get_xml_element_int(test_xml, "Int"))
        with self.assertRaises(AttributeError):
            get_xml_element_int(test_xml, "IntNotExists")
        self.assertEqual(456, get_xml_element_int(test_xml, "IntNotExists", 456))
        with self.assertRaises(InvalidXmlInt):
            get_xml_element_int(test_xml, "NotInt")
        with self.assertRaises(InvalidXmlInt):
            get_xml_element_int(test_xml, "NotInt", 456)


class register(TestCase):
    test_officer = None
    test_user = None
    claim = None

    @classmethod
    def setUpTestData(cls):

        cls.claim = create_test_claim(custom_props={'status': Claim.STATUS_CHECKED, 'feedback_status': Claim.FEEDBACK_SELECTED})

        cls.test_officer = create_test_officer(villages=[cls.claim.insuree.family.location])

        insert_renewals(
            date_from=date.today() + timedelta(days=-3650),
            date_to=date.today() + timedelta(days=7300),
            officer_id=cls.test_officer.id,
            reminding_interval=365,
            location_id=cls.claim.insuree.family.location.id,
            location_levels=4)

    def test_generating_feedback(self):
        class DummyUser:
            id_for_audit = -1
            id = 1
        mock_user = mock.Mock(is_anonymous=False)
        mock_user.has_perm = mock.MagicMock(return_value=True)
        mock_user.is_imis_admin = mock.MagicMock(return_value=False)

        create_feedback_prompt(self.claim, user=DummyUser())
        zip = create_officer_feedbacks_export(mock_user, self.test_officer)
        self.assertNotEqual(zip, None)

    def test_generating_renewal(self):
        mock_user = mock.Mock(is_anonymous=False)
        mock_user.has_perm = mock.MagicMock(return_value=True)
        mock_user.is_imis_admin = mock.MagicMock(return_value=False)
        zip = create_officer_renewals_export(mock_user, self.test_officer)
        self.assertNotEqual(zip, None)
