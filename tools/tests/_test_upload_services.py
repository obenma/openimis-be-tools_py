from unittest.mock import patch
from tempfile import TemporaryFile

from core.test_helpers import create_test_interactive_user
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from medical.models import Service
from medical.test_helpers import create_test_service
from tools.services import parse_xml_services, UploadResult, upload_services, parse_optional_service_fields
from tools.constants import STRATEGY_INSERT, STRATEGY_UPDATE, STRATEGY_INSERT_UPDATE, STRATEGY_INSERT_UPDATE_DELETE
from xml.etree import ElementTree


class UploadServicesParseXMLServicesTestCase(TestCase):

    def test_parse_xml_service_fields_no_code(self):
        xml = b"""
            <Services>
                <Service>
                    <ServiceName>Service code missing</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>S</ServiceLevel>
                    <ServicePrice>42.00</ServicePrice>
                    <ServiceCareType>B</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
            </Services>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Service is missing one of", errors[0])

    def test_parse_xml_service_fields_no_name(self):
        xml = b"""
            <Services>
                <Service>
                    <ServiceCode>NO_NAME</ServiceCode>
                    <ServiceType>p</ServiceType>
                    <ServiceLevel>v</ServiceLevel>
                    <ServicePrice>42.42</ServicePrice>
                    <ServiceCareType>I</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>a</ServiceCategory>
                    <ServiceFrequency>88</ServiceFrequency>
                </Service>
            </Services>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Service is missing one of", errors[0])

    def test_parse_xml_service_fields_no_service_type(self):
        xml = b"""
            <Services>
                <Service>
                    <ServiceCode>NO_TYPE</ServiceCode>
                    <ServiceName>Service type missing</ServiceName>
                    <ServiceLevel>C</ServiceLevel>
                    <ServicePrice>42.42</ServicePrice>
                    <ServiceCareType>I</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
            </Services>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Service is missing one of", errors[0])

    def test_parse_xml_service_fields_no_level(self):
        xml = b"""
            <Services>
                <Service>
                    <ServiceCode>NO_LEVEL</ServiceCode>
                    <ServiceName>Service level missing</ServiceName>
                    <ServiceType>c</ServiceType>
                    <ServicePrice>42.42</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>V</ServiceCategory>
                    <ServiceFrequency/>
                </Service>
            </Services>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Service is missing one of", errors[0])

    def test_parse_xml_service_fields_no_price(self):
        xml = b"""
            <Services>
                <Service>
                    <ServiceCode>NO_PRICE</ServiceCode>
                    <ServiceName>Service price missing</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>h</ServiceLevel>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>V</ServiceCategory>
                    <ServiceFrequency/>
                </Service>
            </Services>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Service is missing one of", errors[0])

    def test_parse_xml_service_fields_no_care_type(self):
        xml = b"""
            <Services>
                <Service>
                    <ServiceCode>NO_CARE_TYPE</ServiceCode>
                    <ServiceName>Service care_type missing</ServiceName>
                    <ServiceType>p</ServiceType>
                    <ServiceLevel>V</ServiceLevel>
                    <ServicePrice>1234</ServicePrice>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>c</ServiceCategory>
                    <ServiceFrequency>2</ServiceFrequency>
                </Service>
            </Services>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Service is missing one of", errors[0])

    def test_parse_xml_service_fields_various_price_errors(self):
        code_1 = "ERROR_PRICE_1"
        code_2 = "ERROR_PRICE_2"
        code_3 = "ERROR_PRICE_3"
        code_ok = "OK"
        xml = f"""
            <Services>
                <Service>
                    <ServiceCode>{code_1}</ServiceCode>
                    <ServiceName>Error in price - wrong decimal separator</ServiceName>
                    <ServiceType>C</ServiceType>
                    <ServiceLevel>s</ServiceLevel>
                    <ServicePrice>123,4</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
                <Service>
                    <ServiceCode>{code_2}</ServiceCode>
                    <ServiceName>Error in price - currency symbol at the end</ServiceName>
                    <ServiceType>c</ServiceType>
                    <ServiceLevel>D</ServiceLevel>
                    <ServicePrice>123.4€</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
                <Service>
                    <ServiceCode>{code_3}</ServiceCode>
                    <ServiceName>Error in price - currency symbol as decimal separator</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>H</ServiceLevel>
                    <ServicePrice>123€4</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
                <Service>
                    <ServiceCode>{code_ok}</ServiceCode>
                    <ServiceName>Proper price, with a '.' for decimal separator and without currency symbol</ServiceName>
                    <ServiceType>p</ServiceType>
                    <ServiceLevel>h</ServiceLevel>
                    <ServicePrice>123.45</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
            </Services>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertTrue(raw_services)
            self.assertEqual(len(raw_services), 1)
            self.assertEqual(raw_services[0]["code"], code_ok)
            self.assertEqual(raw_services[0]["price"], 123.45)

            self.assertTrue(errors)
            self.assertEqual(len(errors), 3)

            self.assertIn("price is invalid", errors[0])
            self.assertIn(code_1, errors[0])

            self.assertIn("price is invalid", errors[1])
            self.assertIn(code_2, errors[1])

            self.assertIn("price is invalid", errors[2])
            self.assertIn(code_3, errors[2])

    def test_parse_xml_service_fields_error_repeated_code(self):
        code_1 = "CODE_1"
        code_2 = "CODE_2"
        xml = f"""
            <Services>
                <Service>
                    <ServiceCode>{code_1}</ServiceCode>
                    <ServiceName>Service 1</ServiceName>
                    <ServiceType>C</ServiceType>
                    <ServiceLevel>H</ServiceLevel>
                    <ServicePrice>0.45</ServicePrice>
                    <ServiceCareType>I</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>5</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>{code_1}</ServiceCode>
                    <ServiceName>Service 1 w/ different values and same code</ServiceName>
                    <ServiceType>c</ServiceType>
                    <ServiceLevel>h</ServiceLevel>
                    <ServicePrice>2.45</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>0</ServiceFemaleCategory>
                    <ServiceAdultCategory>0</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>5</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>{code_2}</ServiceCode>
                    <ServiceName>Service 2</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>V</ServiceLevel>
                    <ServicePrice>1000</ServicePrice>
                    <ServiceCareType>B</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>5</ServiceFrequency>
                </Service>
            </Services>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertTrue(raw_services)
            self.assertEqual(len(raw_services), 2)
            self.assertEqual(raw_services[0]["code"], code_1)
            self.assertEqual(raw_services[1]["code"], code_2)

            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("exists multiple times", errors[0])
            self.assertIn(code_1, errors[0])

    def test_parse_xml_service_fields_error_code_too_small(self):
        xml = b"""
            <Services>
                <Service>
                    <ServiceCode> </ServiceCode>
                    <ServiceName>Service code is a single space that will be trimmed</ServiceName>
                    <ServiceType>p</ServiceType>
                    <ServiceLevel>s</ServiceLevel>
                    <ServicePrice>1234</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>58</ServiceFrequency>
                </Service>
            </Services>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("code is invalid", errors[0])
            self.assertIn("''", errors[0])

    def test_parse_xml_service_fields_error_code_too_long(self):
        long_boi = "THIS_CODE_IS_REALLY_LONG_WHY?"
        xml = f"""
            <Services>
                <Service>
                    <ServiceCode>{long_boi}</ServiceCode>
                    <ServiceName>Service code is a single space that will be trimmed</ServiceName>
                    <ServiceType>C</ServiceType>
                    <ServiceLevel>V</ServiceLevel>
                    <ServicePrice>1234</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
            </Services>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("code is invalid", errors[0])
            self.assertIn(long_boi, errors[0])

    def test_parse_xml_service_fields_error_name_too_small(self):
        xml = b"""
            <Services>
                <Service>
                    <ServiceCode>CODE</ServiceCode>
                    <ServiceName> </ServiceName>
                    <ServiceType>c</ServiceType>
                    <ServiceLevel>v</ServiceLevel>
                    <ServicePrice>1234</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
            </Services>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("name is invalid", errors[0])
            self.assertIn("''", errors[0])

    def test_parse_xml_service_fields_error_name_too_long(self):
        long_boi = "this name is really long, why? Why would anyone prepare a medical " \
                   "service with a name so long, it doesn't make any sense..."
        xml = f"""
            <Services>
                <Service>
                    <ServiceCode>CODE</ServiceCode>
                    <ServiceName>{long_boi}</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>D</ServiceLevel>
                    <ServicePrice>1234</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>S</ServiceCategory>
                    <ServiceFrequency/>
                </Service>
            </Services>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertFalse(raw_services)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("name is invalid", errors[0])
            self.assertIn(long_boi, errors[0])

    def test_parse_xml_service_fields_error_unknown_type(self):
        unknown_type = "O"
        xml = f"""
            <Services>
                <Service>
                    <ServiceCode>P_MAJ</ServiceCode>
                    <ServiceName>Service of type P in capital letter</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>d</ServiceLevel>
                    <ServicePrice>9.87</ServicePrice>
                    <ServiceCareType>I</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>P_MIN</ServiceCode>
                    <ServiceName>Service of type P in small letter</ServiceName>
                    <ServiceType>p</ServiceType>
                    <ServiceLevel>H</ServiceLevel>
                    <ServicePrice>8.76</ServicePrice>
                    <ServiceCareType>I</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>C_MAJ</ServiceCode>
                    <ServiceName>Service of type C in capital letter</ServiceName>
                    <ServiceType>C</ServiceType>
                    <ServiceLevel>h</ServiceLevel>
                    <ServicePrice>7.65</ServicePrice>
                    <ServiceCareType>I</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>C_MIN</ServiceCode>
                    <ServiceName>Service of type C in small letter</ServiceName>
                    <ServiceType>c</ServiceType>
                    <ServiceLevel>S</ServiceLevel>
                    <ServicePrice>6.54</ServicePrice>
                    <ServiceCareType>I</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>O_MIN</ServiceCode>
                    <ServiceName>Service of unknown type</ServiceName>
                    <ServiceType>{unknown_type}</ServiceType>
                    <ServiceLevel>s</ServiceLevel>
                    <ServicePrice>5.43</ServicePrice>
                    <ServiceCareType>B</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
            </Services>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertTrue(raw_services)
            self.assertEqual(len(raw_services), 4)

            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("type is invalid", errors[0])
            self.assertIn(unknown_type, errors[0])

    def test_parse_xml_service_fields_error_unknown_care_type(self):
        unknown_care_type = "K"
        xml = f"""
            <Services>
                <Service>
                    <ServiceCode>I_MAJ</ServiceCode>
                    <ServiceName>Service of care_type I in capital letter</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>V</ServiceLevel>
                    <ServicePrice>9.87</ServicePrice>
                    <ServiceCareType>I</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>s</ServiceCategory>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>I_MIN</ServiceCode>
                    <ServiceName>Service of care_type I in small letter</ServiceName>
                    <ServiceType>p</ServiceType>
                    <ServiceLevel>v</ServiceLevel>
                    <ServicePrice>8.76</ServicePrice>
                    <ServiceCareType>i</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>D</ServiceCategory>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>O_MAJ</ServiceCode>
                    <ServiceName>Service of care_type O in capital letter</ServiceName>
                    <ServiceType>C</ServiceType>
                    <ServiceLevel>D</ServiceLevel>
                    <ServicePrice>7.65</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>d</ServiceCategory>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>O_MIN</ServiceCode>
                    <ServiceName>Service of care_type O in small letter</ServiceName>
                    <ServiceType>c</ServiceType>
                    <ServiceLevel>d</ServiceLevel>
                    <ServicePrice>6.54</ServicePrice>
                    <ServiceCareType>o</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>A</ServiceCategory>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>B_MAJ</ServiceCode>
                    <ServiceName>Service of care_type B in capital letter</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>H</ServiceLevel>
                    <ServicePrice>5.43</ServicePrice>
                    <ServiceCareType>B</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>a</ServiceCategory>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>B_MIN</ServiceCode>
                    <ServiceName>Service of care_type B in small letter</ServiceName>
                    <ServiceType>c</ServiceType>
                    <ServiceLevel>h</ServiceLevel>
                    <ServicePrice>4.32</ServicePrice>
                    <ServiceCareType>b</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>H</ServiceCategory>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
                <Service>
                    <ServiceCode>K_MAJ</ServiceCode>
                    <ServiceName>Service of unknown care_type</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>S</ServiceLevel>
                    <ServicePrice>3.21</ServicePrice>
                    <ServiceCareType>{unknown_care_type}</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory>h</ServiceCategory>
                    <ServiceFrequency>7</ServiceFrequency>
                </Service>
            </Services>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertTrue(raw_services)
            self.assertEqual(len(raw_services), 6)

            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("care type is invalid", errors[0])
            self.assertIn(unknown_care_type, errors[0])

    def test_parse_xml_service_fields_mixed_errors_and_success(self):
        code_ok_1 = "CODE_1"
        code_ok_2 = "CODE_2"
        code_ok_3 = "CODE_3"

        long_name = "this name is really long, why? Why would anyone prepare a medical service " \
                    "with a name so long, it doesn't make any sense..."
        unknown_care_type = "K"
        xml = f"""
            <Services>
                <Service>
                    <ServiceCode>CODE</ServiceCode>
                    <ServiceName>{long_name}</ServiceName>
                    <ServiceType>p</ServiceType>
                    <ServiceLevel>s</ServiceLevel>
                    <ServicePrice>1234</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
                <Service>
                    <ServiceCode>{code_ok_1}</ServiceCode>
                    <ServiceName>Valid Service 1 - no error</ServiceName>
                    <ServiceType>C</ServiceType>
                    <ServiceLevel>V</ServiceLevel>
                    <ServicePrice>9.87</ServicePrice>
                    <ServiceCareType>I</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
                <Service>
                    <ServiceCode>K_MAJ</ServiceCode>
                    <ServiceName>Service of unknown care_type</ServiceName>
                    <ServiceType>c</ServiceType>
                    <ServiceLevel>v</ServiceLevel>
                    <ServicePrice>3.21</ServicePrice>
                    <ServiceCareType>{unknown_care_type}</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
                <Service>
                    <ServiceCode>{code_ok_2}</ServiceCode>
                    <ServiceName>Valid Service 2 - no error</ServiceName>
                    <ServiceType>P</ServiceType>
                    <ServiceLevel>D</ServiceLevel>
                    <ServicePrice>555.55</ServicePrice>
                    <ServiceCareType>b</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
                <Service>
                    <ServiceCode>{code_ok_3}</ServiceCode>
                    <ServiceName>Valid Service 3 - no error</ServiceName>
                    <ServiceType>p</ServiceType>
                    <ServiceLevel>d</ServiceLevel>
                    <ServicePrice>489.54</ServicePrice>
                    <ServiceCareType>O</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
                <Service>
                    <ServiceName>Service without code</ServiceName>
                    <ServiceType>C</ServiceType>
                    <ServicePrice>3700.88</ServicePrice>
                    <ServiceLevel>H</ServiceLevel>
                    <ServiceCareType>o</ServiceCareType>
                    <ServiceMaleCategory>1</ServiceMaleCategory>
                    <ServiceFemaleCategory>1</ServiceFemaleCategory>
                    <ServiceAdultCategory>1</ServiceAdultCategory>
                    <ServiceMinorCategory>1</ServiceMinorCategory>
                    <ServiceCategory/>
                    <ServiceFrequency/>
                </Service>
            </Services>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_services, errors = parse_xml_services(et)

            self.assertTrue(raw_services)
            self.assertEqual(len(raw_services), 3)
            self.assertIn(code_ok_1, raw_services[0]["code"])
            self.assertIn(code_ok_2, raw_services[1]["code"])
            self.assertIn(code_ok_3, raw_services[2]["code"])

            self.assertTrue(errors)
            self.assertEqual(len(errors), 3)
            self.assertIn("name is invalid", errors[0])
            self.assertIn(long_name, errors[0])
            self.assertIn("care type is invalid", errors[1])
            self.assertIn(unknown_care_type, errors[1])
            self.assertIn("Service is missing one of", errors[2])


class UploadServicesParseOptionalFieldsTestCase(TestCase):

    def test_parse_optional_service_fields_all_empty(self):
        xml = """
            <Service>
                <ServiceCategory/>
                <ServiceFrequency/>
            </Service>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_service_fields(root, "EMPTY")

            self.assertFalse(optional_fields)
            self.assertFalse(error)

    def test_parse_optional_service_fields_all_filled(self):
        xml = """
            <Service>
                <ServiceCategory>O</ServiceCategory>
                <ServiceFrequency>5</ServiceFrequency>
            </Service>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_service_fields(root, "FILLED")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 2)
            self.assertIn("frequency", optional_fields)
            self.assertIn("category", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_service_fields_filled_and_empty_frq(self):
        xml = """
            <Service>
                <ServiceCategory/>
                <ServiceFrequency>78</ServiceFrequency>
            </Service>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_service_fields(root, "1/2")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 1)
            self.assertIn("frequency", optional_fields)
            self.assertNotIn("category", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_service_fields_filled_and_empty_cat(self):
        xml = """
            <Service>
                <ServiceCategory>o</ServiceCategory>
                <ServiceFrequency/>
            </Service>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_service_fields(root, "1/3")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 1)
            self.assertIn("category", optional_fields)
            self.assertNotIn("frequency", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_service_fields_error_frequency(self):
        xml = """
            <Service>
                <ServiceCategory>V</ServiceCategory>
                <ServiceFrequency>5.55</ServiceFrequency>
            </Service>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            code = "ERROR_FRQ"
            optional_fields, error = parse_optional_service_fields(root, code)

            self.assertNotIn("frequency", optional_fields)
            self.assertTrue(error)
            self.assertIn("frequency is invalid", error)
            self.assertIn(code, error)


class UploadServicesTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(username="testServicesAdmin")

    @patch("tools.services.parse_xml_services")
    def test_upload_services_multiple_insert_dry_run(self, mock_parsing):
        dry_run = True
        strategy = STRATEGY_INSERT
        existing_code = "A1"
        raw_services = [
            {
                "code": "CODE_1",
                "name": "Valid Service 1 - no error",
            },
            {
                "code": "CODE_2",
                "name": "Valid Service 2 - no error",
            },
            {
                "code": existing_code,
                "name": "Invalid Service - code already exists",
            }
        ]
        errors = []
        mock_parsing.return_value = raw_services, errors

        expected_errors = [
            f"Service '{existing_code}' already exists"
        ]
        expected = UploadResult(
            errors=expected_errors,
            sent=3,
            created=2,
            updated=0,
            deleted=0,
        )
        result = upload_services(self.admin_user, "xml", strategy, dry_run)

        self.assertEqual(expected, result)

    @patch("tools.services.parse_xml_services")
    def test_upload_services_multiple_update_dry_run(self, mock_parsing):
        dry_run = True
        strategy = STRATEGY_UPDATE
        existing_code_1 = "A1"
        existing_code_2 = "I117"
        error_code = "ERROR"
        raw_services = [
            {
                "code": existing_code_1,
                "name": "Valid Service 1 - no error",
            },
            {
                "code": error_code,
                "name": "Invalid Service - code doesn't exists",
            },
            {
                "code": existing_code_2,
                "name": "Valid Service 2 - no error",
            },
        ]
        errors = []
        mock_parsing.return_value = raw_services, errors

        expected_errors = [
            f"Service '{error_code}' does not exist"
        ]
        expected = UploadResult(
            errors=expected_errors,
            sent=3,
            created=0,
            updated=2,
            deleted=0,
        )
        result = upload_services(self.admin_user, "xml", strategy, dry_run)

        self.assertEqual(expected, result)

    @patch("tools.services.parse_xml_services")
    def test_upload_services_multiple_insert_update_dry_run(self, mock_parsing):
        dry_run = True
        strategy = STRATEGY_INSERT_UPDATE
        raw_services = [
            {
                "code": "CODE_1",
                "name": "New Service 1",
            },
            {
                "code": "CODE_2",
                "name": "New Service 2",
            },
            {
                "code": "G1",
                "name": "Existing Service 1",
            },
            {
                "code": "CODE_3",
                "name": "New Service 3",
            },
            {
                "code": "G34",
                "name": "Existing Service 2",
            },
        ]
        errors = []
        mock_parsing.return_value = raw_services, errors

        expected = UploadResult(
            errors=errors,
            sent=5,
            created=3,
            updated=2,
            deleted=0,
        )
        result = upload_services(self.admin_user, "xml", strategy, dry_run)

        self.assertEqual(expected, result)

    @patch("tools.services.parse_xml_services")
    def test_upload_services_multiple_insert_update_delete_dry_run(self, mock_parsing):
        dry_run = True
        strategy = STRATEGY_INSERT_UPDATE_DELETE
        raw_services = [
            {
                "code": "CODE_1",
                "name": "New Service 1",
            },
            {
                "code": "CODE_2",
                "name": "New Service 2",
            },
            {
                "code": "A1",
                "name": "Existing Service 1",
            },
            {
                "code": "CODE_3",
                "name": "New Service 3",
            },
            {
                "code": "G60",
                "name": "Existing Service 2",
            },
        ]
        errors = []
        mock_parsing.return_value = raw_services, errors

        before_total_services = Service.objects.filter(*Service.filter_validity()).count()
        expected_deleted = before_total_services - 2

        expected = UploadResult(
            errors=errors,
            sent=5,
            created=3,
            updated=2,
            deleted=expected_deleted,
        )
        result = upload_services(self.admin_user, "xml", strategy, dry_run)

        self.assertEqual(expected, result)

    @patch("tools.services.parse_xml_services")
    def test_upload_services_multiple_insert(self, mock_parsing):
        # setup - preparing data that will be inserted
        dry_run = False
        strategy = STRATEGY_INSERT
        existing_code = "A1"
        new_code_1 = "CODE_1"
        new_code_2 = "CODE_2"
        raw_services = [
            {
                "code": new_code_1,
                "name": "Valid Service 1 - no error",
                "type": "P",
                "level": "S",
                "price": 489.54,
                "care_type": "O",
                "patient_category": 15,
                "category": "H",
                "frequency": 5,
            },
            {
                "code": new_code_2,
                "name": "Valid Service 2 - no error",
                "type": "C",
                "level": "s",
                "price": 499.54,
                "care_type": "O",
                "patient_category": 5,
                "category": "c",
                "frequency": 57,
            },
            {
                "code": existing_code,
                "name": "Invalid Service - code already exists",
                "type": "p",
                "level": "V",
                "price": 599.54,
                "care_type": "B",
                "patient_category": 7,
                "category": "O",
                "frequency": 7,
            }
        ]
        errors = []
        mock_parsing.return_value = raw_services, errors

        expected_errors = [
            f"Service '{existing_code}' already exists"
        ]
        expected = UploadResult(
            errors=expected_errors,
            sent=3,
            created=2,
            updated=0,
            deleted=0,
        )
        total_services_before = Service.objects.filter(*Service.filter_validity()).count()

        # Inserting
        result = upload_services(self.admin_user, "xml", strategy, dry_run)
        total_services_after = Service.objects.filter(*Service.filter_validity()).count()

        self.assertEqual(expected, result)
        self.assertEqual(total_services_before + 2, total_services_after)

        # Making sure the new services don't stay in the DB
        new_service1 = Service.objects.get(code=new_code_1)
        new_service1.delete()
        new_service2 = Service.objects.get(code=new_code_2)
        new_service2.delete()

    @patch("tools.services.parse_xml_services")
    def test_upload_services_multiple_update(self, mock_parsing):
        # setup - creating services that will be updated
        new_code_1 = "CODE_1"
        old_name_1 = "new Service old name 0001"
        new_service_1_props = {
            "code": new_code_1,
            "name": old_name_1,
        }
        create_test_service(category="D", custom_props=new_service_1_props)

        new_code_2 = "CODE_2"
        old_name_2 = "new Service old name 0002"
        new_service_2_props = {
            "code": new_code_2,
            "name": old_name_2,
        }
        create_test_service(category="D", custom_props=new_service_2_props)

        # setup - preparing values used for the update
        dry_run = False
        strategy = STRATEGY_UPDATE
        new_name_1 = "new Service new name 0001"
        new_name_2 = "new Service new name 0002"
        non_existing_code = "ERROR"
        raw_services = [
            {
                "code": new_code_1,
                "name": new_name_1,
                "type": "c",
                "level": "v",
                "price": 66.54,
                "care_type": "i",
                "patient_category": 15,
                "category": "D",
            },
            {
                "code": new_code_2,
                "name": new_name_2,
                "type": "P",
                "level": "D",
                "price": 66.54,
                "care_type": "I",
                "patient_category": 15,
                "frequency": 1,
            },
            {
                "code": non_existing_code,
                "name": "error - this can't be updated",
                "type": "p",
                "level": "d",
                "price": 66.54,
                "care_type": "I",
                "patient_category": 15,
            }
        ]
        errors = []
        mock_parsing.return_value = raw_services, errors
        expected_errors = [
            f"Service '{non_existing_code}' does not exist"
        ]
        expected = UploadResult(
            errors=expected_errors,
            sent=3,
            created=0,
            updated=2,
            deleted=0,
        )
        total_services_before = Service.objects.filter(*Service.filter_validity()).count()

        # update
        result = upload_services(self.admin_user, "xml", strategy, dry_run)
        total_services_after = Service.objects.filter(*Service.filter_validity()).count()

        self.assertEqual(expected, result)
        self.assertEqual(total_services_before, total_services_after)

        # Making sure the names have been updated + deleting the new services to make sure they don't stay in the DB
        db_new_service_1 = Service.objects.get(code=new_code_1, validity_to=None)
        self.assertEqual(db_new_service_1.name, new_name_1)
        db_new_service_1.delete()

        db_new_service_2 = Service.objects.get(code=new_code_2, validity_to=None)
        self.assertEqual(db_new_service_2.name, new_name_2)
        db_new_service_2.delete()

    @patch("tools.services.parse_xml_services")
    def test_upload_services_multiple_insert_update(self, mock_parsing):
        # setup - creating services that will be updated
        update_code_1 = "U_1"
        old_name_1 = "update Service old name 0001"
        update_service_1_props = {
            "code": update_code_1,
            "name": old_name_1,
        }
        create_test_service(category="D", custom_props=update_service_1_props)

        update_code_2 = "U_2"
        old_name_2 = "update Service old name 0002"
        update_service_2_props = {
            "code": update_code_2,
            "name": old_name_2,
        }
        create_test_service(category="D", custom_props=update_service_2_props)

        # setup - preparing values used for the update
        dry_run = False
        strategy = STRATEGY_INSERT_UPDATE
        new_name_1 = "update Service new name 0001"
        new_name_2 = "update Service new name 0002"
        insert_code_1 = "I_1"
        insert_code_2 = "I_2"
        raw_services = [
            {
                "code": insert_code_1,
                "name": "insert Service 1",
                "type": "C",
                "level": "H",
                "price": 65.54,
                "care_type": "b",
                "patient_category": 15,
                "category": "d",
            },
            {
                "code": update_code_1,
                "name": new_name_1,
                "type": "c",
                "level": "h",
                "price": 66.54,
                "care_type": "i",
                "patient_category": 15,
                "category": "D",
                "frequency": 6,
            },
            {
                "code": update_code_2,
                "name": new_name_2,
                "type": "P",
                "level": "S",
                "price": 66.54,
                "care_type": "I",
                "patient_category": 15,
            },
            {
                "code": insert_code_2,
                "name": "insert Service 2",
                "type": "p",
                "level": "s",
                "price": 60.54,
                "care_type": "b",
                "patient_category": 15,
            },
        ]
        errors = []
        mock_parsing.return_value = raw_services, errors
        expected = UploadResult(
            errors=errors,
            sent=4,
            created=2,
            updated=2,
            deleted=0,
        )
        total_services_before = Service.objects.filter(*Service.filter_validity()).count()

        # insert-update
        result = upload_services(self.admin_user, "xml", strategy, dry_run)
        total_services_after = Service.objects.filter(*Service.filter_validity()).count()

        self.assertEqual(expected, result)
        self.assertEqual(total_services_before + 2, total_services_after)

        # Making sure the names have been updated + deleting the update services to make sure they don't stay in the DB
        db_update_service_1 = Service.objects.get(code=update_code_1, validity_to=None)
        self.assertEqual(db_update_service_1.name, new_name_1)
        db_update_service_1.delete()

        db_update_service_2 = Service.objects.get(code=update_code_2, validity_to=None)
        self.assertEqual(db_update_service_2.name, new_name_2)
        db_update_service_2.delete()

        # Also deleting the insert services to make sure they don't stay in the DB
        db_insert_service_1 = Service.objects.get(code=insert_code_1, validity_to=None)
        db_insert_service_1.delete()
        db_insert_service_2 = Service.objects.get(code=insert_code_2, validity_to=None)
        db_insert_service_2.delete()

    @patch("tools.services.parse_xml_services")
    def test_upload_services_multiple_insert_update_delete(self, mock_parsing):
        # setup - fetching initial DB services in order not to delete them
        services = Service.objects.filter(*Service.filter_validity()).all()
        services_to_not_delete = []
        for service in services:
            service_dict = service.__dict__
            service_dict.pop("id")
            service_dict.pop("uuid")
            service_dict.pop("_state")
            service_dict.pop("validity_from")
            service_dict.pop("validity_to")
            service_dict.pop("legacy_id")
            services_to_not_delete.append(service_dict)

        # setup - creating services that will be updated & deleted
        update_code = "U_1"
        old_name = "update Service old name 0001"
        update_service_props = {
            "code": update_code,
            "name": old_name,
        }
        create_test_service(category="D", custom_props=update_service_props)

        delete_code = "D_1"
        delete_service_props = {
            "code": delete_code,
            "name": "Service do be deleted",
        }
        create_test_service(category="D", custom_props=delete_service_props)

        # setup - preparing values used for the tests
        dry_run = False
        strategy = STRATEGY_INSERT_UPDATE_DELETE
        update_new_name = "update Service new name 0001"
        insert_code_1 = "I_1"
        insert_code_2 = "I_2"
        new_services = [
            {
                "code": insert_code_1,
                "name": "insert Service 1",
                "type": "p",
                "level": "V",
                "price": 65.54,
                "care_type": "b",
                "patient_category": 15,
                "category": "s",
            },
            {
                "code": update_code,
                "name": update_new_name,
                "type": "c",
                "level": "v",
                "price": 66.54,
                "care_type": "i",
                "patient_category": 15,
                "category": "S",
                "frequency": 6,
            },
            {
                "code": insert_code_2,
                "name": "insert Service 2",
                "type": "c",
                "level": "D",
                "price": 60.54,
                "care_type": "b",
                "patient_category": 15,
            },
        ]
        raw_services = new_services + services_to_not_delete
        errors = []
        mock_parsing.return_value = raw_services, errors

        total_updated = len(services_to_not_delete) + 1
        total_sent = total_updated + 2
        expected = UploadResult(
            errors=errors,
            sent=total_sent,
            created=2,
            updated=total_updated,
            deleted=1,
        )
        total_services_before = Service.objects.filter(*Service.filter_validity()).count()

        # insert update delete
        result = upload_services(self.admin_user, "xml", strategy, dry_run)
        total_services_after = Service.objects.filter(*Service.filter_validity()).count()

        self.assertEqual(expected, result)
        # 2 inserts and 1 deletion
        self.assertEqual(total_services_before + 1, total_services_after)

        with self.assertRaises(ObjectDoesNotExist):
            Service.objects.get(code=delete_code, validity_to=None)

        # Making sure the name has been updated + deleting the services to make sure they don't stay in the DB
        db_update_service = Service.objects.get(code=update_code, validity_to=None)
        self.assertEqual(db_update_service.name, update_new_name)
        db_update_service.delete()

        db_insert_service_1 = Service.objects.get(code=insert_code_1, validity_to=None)
        db_insert_service_1.delete()
        db_insert_service_2 = Service.objects.get(code=insert_code_2, validity_to=None)
        db_insert_service_2.delete()
