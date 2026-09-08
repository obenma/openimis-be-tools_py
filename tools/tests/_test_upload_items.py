from unittest.mock import patch
from tempfile import TemporaryFile

from core.test_helpers import create_test_interactive_user
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from medical.models import Item
from medical.test_helpers import create_test_item
from tools.services import parse_xml_items, UploadResult, upload_items, parse_optional_item_fields
from tools.constants import STRATEGY_INSERT, STRATEGY_UPDATE, STRATEGY_INSERT_UPDATE, STRATEGY_INSERT_UPDATE_DELETE
from xml.etree import ElementTree


class UploadItemsParseXMLItemsTestCase(TestCase):

    def test_parse_xml_item_fields_no_code(self):
        xml = b"""
            <Items>
                <Item>
                    <ItemName>Item code missing</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>42.00</ItemPrice>
                    <ItemCareType>B</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemQuantity/>
                    <ItemPackage/>
                    <ItemFrequency/>
                </Item>
            </Items>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertFalse(raw_items)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Item is missing one of", errors[0])

    def test_parse_xml_item_fields_no_name(self):
        xml = b"""
            <Items>
                <Item>
                    <ItemCode>NO_NAME</ItemCode>
                    <ItemType>M</ItemType>
                    <ItemPrice>42.42</ItemPrice>
                    <ItemCareType>I</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Nice package</ItemPackage>
                    <ItemQuantity/>
                    <ItemFrequency>88</ItemFrequency>
                </Item>
            </Items>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertFalse(raw_items)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Item is missing one of", errors[0])

    def test_parse_xml_item_fields_no_item_type(self):
        xml = b"""
            <Items>
                <Item>
                    <ItemCode>NO_TYPE</ItemCode>
                    <ItemName>Item type missing</ItemName>
                    <ItemPrice>42.42</ItemPrice>
                    <ItemCareType>I</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
            </Items>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertFalse(raw_items)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Item is missing one of", errors[0])

    def test_parse_xml_item_fields_no_price(self):
        xml = b"""
            <Items>
                <Item>
                    <ItemCode>NO_PRICE</ItemCode>
                    <ItemName>Item price missing</ItemName>
                    <ItemType>D</ItemType>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Something</ItemPackage>
                    <ItemQuantity>8.99</ItemQuantity>
                    <ItemFrequency/>
                </Item>
            </Items>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertFalse(raw_items)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Item is missing one of", errors[0])

    def test_parse_xml_item_fields_no_care_type(self):
        xml = b"""
            <Items>
                <Item>
                    <ItemCode>NO_CARE_TYPE</ItemCode>
                    <ItemName>Item care_type missing</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>1234</ItemPrice>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>1000 TABLETS</ItemPackage>
                    <ItemQuantity>42.44</ItemQuantity>
                    <ItemFrequency>2</ItemFrequency>
                </Item>
            </Items>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertFalse(raw_items)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("Item is missing one of", errors[0])

    def test_parse_xml_item_fields_various_price_errors(self):
        code_1 = "ERROR_PRICE_1"
        code_2 = "ERROR_PRICE_2"
        code_3 = "ERROR_PRICE_3"
        code_ok = "OK"
        xml = f"""
            <Items>
                <Item>
                    <ItemCode>{code_1}</ItemCode>
                    <ItemName>Error in price - wrong decimal separator</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>123,4</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemQuantity/>
                    <ItemPackage/>
                    <ItemFrequency/>
                </Item>
                <Item>
                    <ItemCode>{code_2}</ItemCode>
                    <ItemName>Error in price - currency symbol at the end</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>123.4€</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemQuantity/>
                    <ItemPackage/>
                    <ItemFrequency/>
                </Item>
                <Item>
                    <ItemCode>{code_3}</ItemCode>
                    <ItemName>Error in price - currency symbol as decimal separator</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>123€4</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemQuantity/>
                    <ItemPackage/>
                    <ItemFrequency/>
                </Item>
                <Item>
                    <ItemCode>{code_ok}</ItemCode>
                    <ItemName>Proper price, with a '.' for decimal separator and without currency symbol</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>123.45</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemQuantity/>
                    <ItemPackage/>
                    <ItemFrequency/>
                </Item>
            </Items>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertTrue(raw_items)
            self.assertEqual(len(raw_items), 1)
            self.assertEqual(raw_items[0]["code"], code_ok)
            self.assertEqual(raw_items[0]["price"], 123.45)

            self.assertTrue(errors)
            self.assertEqual(len(errors), 3)

            self.assertIn("price is invalid", errors[0])
            self.assertIn(code_1, errors[0])

            self.assertIn("price is invalid", errors[1])
            self.assertIn(code_2, errors[1])

            self.assertIn("price is invalid", errors[2])
            self.assertIn(code_3, errors[2])

    def test_parse_xml_item_fields_error_repeated_code(self):
        code_1 = "CODE_1"
        code_2 = "CODE_2"
        xml = f"""
            <Items>
                <Item>
                    <ItemCode>{code_1}</ItemCode>
                    <ItemName>Item 1</ItemName>
                    <ItemType>M</ItemType>
                    <ItemPrice>0.45</ItemPrice>
                    <ItemCareType>I</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity/>
                    <ItemFrequency>5</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>{code_1}</ItemCode>
                    <ItemName>Item 1 w/ different values and same code</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>2.45</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>0</ItemFemaleCategory>
                    <ItemAdultCategory>0</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity/>
                    <ItemFrequency>5</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>{code_2}</ItemCode>
                    <ItemName>Item 2</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>1000</ItemPrice>
                    <ItemCareType>B</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity/>
                    <ItemFrequency>5</ItemFrequency>
                </Item>
            </Items>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertTrue(raw_items)
            self.assertEqual(len(raw_items), 2)
            self.assertEqual(raw_items[0]["code"], code_1)
            self.assertEqual(raw_items[1]["code"], code_2)

            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("exists multiple times", errors[0])
            self.assertIn(code_1, errors[0])

    def test_parse_xml_item_fields_error_code_too_small(self):
        xml = b"""
            <Items>
                <Item>
                    <ItemCode> </ItemCode>
                    <ItemName>Item code is a single space that will be trimmed</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>1234</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity/>
                    <ItemFrequency>58</ItemFrequency>
                </Item>
            </Items>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertFalse(raw_items)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("code is invalid", errors[0])
            self.assertIn("''", errors[0])

    def test_parse_xml_item_fields_error_code_too_long(self):
        long_boi = "THIS_CODE_IS_REALLY_LONG_WHY?"
        xml = f"""
            <Items>
                <Item>
                    <ItemCode>{long_boi}</ItemCode>
                    <ItemName>Item code is a single space that will be trimmed</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>1234</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>88.25</ItemQuantity>
                    <ItemFrequency/>
                </Item>
            </Items>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertFalse(raw_items)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("code is invalid", errors[0])
            self.assertIn(long_boi, errors[0])

    def test_parse_xml_item_fields_error_name_too_small(self):
        xml = b"""
            <Items>
                <Item>
                    <ItemCode>CODE</ItemCode>
                    <ItemName> </ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>1234</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>882.5</ItemQuantity>
                    <ItemFrequency/>
                </Item>
            </Items>
        """
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertFalse(raw_items)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("name is invalid", errors[0])
            self.assertIn("''", errors[0])

    def test_parse_xml_item_fields_error_name_too_long(self):
        long_boi = "this name is really long, why? Why would anyone prepare a medical " \
                   "item with a name so long, it doesn't make any sense..."
        xml = f"""
            <Items>
                <Item>
                    <ItemCode>CODE</ItemCode>
                    <ItemName>{long_boi}</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>1234</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Pikachu</ItemPackage>
                    <ItemQuantity/>
                    <ItemFrequency/>
                </Item>
            </Items>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertFalse(raw_items)
            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("name is invalid", errors[0])
            self.assertIn(long_boi, errors[0])

    def test_parse_xml_item_fields_error_unknown_type(self):
        unknown_type = "O"
        xml = f"""
            <Items>
                <Item>
                    <ItemCode>M_MAJ</ItemCode>
                    <ItemName>Item of type M in capital letter</ItemName>
                    <ItemType>M</ItemType>
                    <ItemPrice>9.87</ItemPrice>
                    <ItemCareType>I</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>M_MIN</ItemCode>
                    <ItemName>Item of type M in small letter</ItemName>
                    <ItemType>m</ItemType>
                    <ItemPrice>8.76</ItemPrice>
                    <ItemCareType>I</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>D_MAJ</ItemCode>
                    <ItemName>Item of type D in capital letter</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>7.65</ItemPrice>
                    <ItemCareType>I</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>D_MIN</ItemCode>
                    <ItemName>Item of type D in small letter</ItemName>
                    <ItemType>d</ItemType>
                    <ItemPrice>6.54</ItemPrice>
                    <ItemCareType>I</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>O_MIN</ItemCode>
                    <ItemName>Item of unknown type</ItemName>
                    <ItemType>{unknown_type}</ItemType>
                    <ItemPrice>5.43</ItemPrice>
                    <ItemCareType>B</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
            </Items>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertTrue(raw_items)
            self.assertEqual(len(raw_items), 4)

            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("type is invalid", errors[0])
            self.assertIn(unknown_type, errors[0])

    def test_parse_xml_item_fields_error_unknown_care_type(self):
        unknown_care_type = "K"
        xml = f"""
            <Items>
                <Item>
                    <ItemCode>I_MAJ</ItemCode>
                    <ItemName>Item of care_type I in capital letter</ItemName>
                    <ItemType>M</ItemType>
                    <ItemPrice>9.87</ItemPrice>
                    <ItemCareType>I</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Mew</ItemPackage>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>I_MIN</ItemCode>
                    <ItemName>Item of care_type I in small letter</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>8.76</ItemPrice>
                    <ItemCareType>i</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Mewtwo</ItemPackage>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>O_MAJ</ItemCode>
                    <ItemName>Item of care_type O in capital letter</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>7.65</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Snorlax</ItemPackage>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>O_MIN</ItemCode>
                    <ItemName>Item of care_type O in small letter</ItemName>
                    <ItemType>m</ItemType>
                    <ItemPrice>6.54</ItemPrice>
                    <ItemCareType>o</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Chansey</ItemPackage>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>B_MAJ</ItemCode>
                    <ItemName>Item of care_type B in capital letter</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>5.43</ItemPrice>
                    <ItemCareType>B</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Charizard</ItemPackage>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>B_MIN</ItemCode>
                    <ItemName>Item of care_type B in small letter</ItemName>
                    <ItemType>m</ItemType>
                    <ItemPrice>4.32</ItemPrice>
                    <ItemCareType>b</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Machop</ItemPackage>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
                <Item>
                    <ItemCode>K_MAJ</ItemCode>
                    <ItemName>Item of unknown care_type</ItemName>
                    <ItemType>M</ItemType>
                    <ItemPrice>3.21</ItemPrice>
                    <ItemCareType>{unknown_care_type}</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage>Tortank</ItemPackage>
                    <ItemQuantity>1.25</ItemQuantity>
                    <ItemFrequency>7</ItemFrequency>
                </Item>
            </Items>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertTrue(raw_items)
            self.assertEqual(len(raw_items), 6)

            self.assertTrue(errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("care type is invalid", errors[0])
            self.assertIn(unknown_care_type, errors[0])

    def test_parse_xml_item_fields_mixed_errors_and_success(self):
        code_ok_1 = "CODE_1"
        code_ok_2 = "CODE_2"
        code_ok_3 = "CODE_3"

        long_name = "this name is really long, why? Why would anyone prepare a medical item " \
                    "with a name so long, it doesn't make any sense..."
        unknown_care_type = "K"
        xml = f"""
            <Items>
                <Item>
                    <ItemCode>CODE</ItemCode>
                    <ItemName>{long_name}</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>1234</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>88.25</ItemQuantity>
                    <ItemFrequency/>
                </Item>
                <Item>
                    <ItemCode>{code_ok_1}</ItemCode>
                    <ItemName>Valid item 1 - no error</ItemName>
                    <ItemType>M</ItemType>
                    <ItemPrice>9.87</ItemPrice>
                    <ItemCareType>I</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>88.25</ItemQuantity>
                    <ItemFrequency/>
                </Item>
                <Item>
                    <ItemCode>K_MAJ</ItemCode>
                    <ItemName>Item of unknown care_type</ItemName>
                    <ItemType>M</ItemType>
                    <ItemPrice>3.21</ItemPrice>
                    <ItemCareType>{unknown_care_type}</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>88.25</ItemQuantity>
                    <ItemFrequency/>
                </Item>
                <Item>
                    <ItemCode>{code_ok_2}</ItemCode>
                    <ItemName>Valid item 2 - no error</ItemName>
                    <ItemType>d</ItemType>
                    <ItemPrice>555.55</ItemPrice>
                    <ItemCareType>b</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>88.25</ItemQuantity>
                    <ItemFrequency/>
                </Item>
                <Item>
                    <ItemCode>{code_ok_3}</ItemCode>
                    <ItemName>Valid item 3 - no error</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>489.54</ItemPrice>
                    <ItemCareType>O</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>88.25</ItemQuantity>
                    <ItemFrequency/>
                </Item>
                <Item>
                    <ItemName>Item without code</ItemName>
                    <ItemType>D</ItemType>
                    <ItemPrice>3700.88</ItemPrice>
                    <ItemCareType>o</ItemCareType>
                    <ItemMaleCategory>1</ItemMaleCategory>
                    <ItemFemaleCategory>1</ItemFemaleCategory>
                    <ItemAdultCategory>1</ItemAdultCategory>
                    <ItemMinorCategory>1</ItemMinorCategory>
                    <ItemPackage/>
                    <ItemQuantity>88.25</ItemQuantity>
                    <ItemFrequency/>
                </Item>
            </Items>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)

            raw_items, errors = parse_xml_items(et)

            self.assertTrue(raw_items)
            self.assertEqual(len(raw_items), 3)
            self.assertIn(code_ok_1, raw_items[0]["code"])
            self.assertIn(code_ok_2, raw_items[1]["code"])
            self.assertIn(code_ok_3, raw_items[2]["code"])

            self.assertTrue(errors)
            self.assertEqual(len(errors), 3)
            self.assertIn("name is invalid", errors[0])
            self.assertIn(long_name, errors[0])
            self.assertIn("care type is invalid", errors[1])
            self.assertIn(unknown_care_type, errors[1])
            self.assertIn("Item is missing one of", errors[2])


class UploadItemsParseOptionalFieldsTestCase(TestCase):

    def test_parse_optional_item_fields_all_empty(self):
        xml = """
            <Item>
                <ItemQuantity/>
                <ItemPackage/>
                <ItemFrequency/>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_item_fields(root, "EMPTY")

            self.assertFalse(optional_fields)
            self.assertFalse(error)

    def test_parse_optional_item_fields_all_filled(self):
        xml = """
            <Item>
                <ItemPackage>1000 TABLETS</ItemPackage>
                <ItemQuantity>42.00</ItemQuantity>
                <ItemFrequency>5</ItemFrequency>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_item_fields(root, "FILLED")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 3)
            self.assertIn("frequency", optional_fields)
            self.assertIn("quantity", optional_fields)
            self.assertIn("package", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_item_fields_filled_and_empty_frq(self):
        xml = """
            <Item>
                <ItemPackage/>
                <ItemQuantity/>
                <ItemFrequency>5</ItemFrequency>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_item_fields(root, "1/3")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 1)
            self.assertIn("frequency", optional_fields)
            self.assertNotIn("quantity", optional_fields)
            self.assertNotIn("package", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_item_fields_filled_and_empty_qty(self):
        xml = """
            <Item>
                <ItemPackage/>
                <ItemQuantity>88.25</ItemQuantity>
                <ItemFrequency/>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_item_fields(root, "1/3")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 1)
            self.assertIn("quantity", optional_fields)
            self.assertNotIn("frequency", optional_fields)
            self.assertNotIn("package", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_item_fields_filled_and_empty_pkg(self):
        xml = """
            <Item>
                <ItemPackage>Great package</ItemPackage>
                <ItemQuantity/>
                <ItemFrequency/>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_item_fields(root, "1/3")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 1)
            self.assertIn("package", optional_fields)
            self.assertNotIn("quantity", optional_fields)
            self.assertNotIn("frequency", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_item_fields_filled_and_empty_frq_qty(self):
        xml = """
            <Item>
                <ItemPackage/>
                <ItemQuantity>1.25</ItemQuantity>
                <ItemFrequency>7</ItemFrequency>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_item_fields(root, "2/3")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 2)
            self.assertIn("frequency", optional_fields)
            self.assertIn("quantity", optional_fields)
            self.assertNotIn("package", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_item_fields_filled_and_empty_frq_pkg(self):
        xml = """
            <Item>
                <ItemPackage>Nice package</ItemPackage>
                <ItemQuantity/>
                <ItemFrequency>88</ItemFrequency>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_item_fields(root, "2/3")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 2)
            self.assertIn("frequency", optional_fields)
            self.assertIn("package", optional_fields)
            self.assertNotIn("quantity", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_item_fields_filled_and_empty_qty_pkg(self):
        xml = """
            <Item>
                <ItemPackage>Nice package</ItemPackage>
                <ItemQuantity>8.99</ItemQuantity>
                <ItemFrequency/>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            optional_fields, error = parse_optional_item_fields(root, "2/3")

            self.assertTrue(optional_fields)
            self.assertEqual(len(optional_fields), 2)
            self.assertIn("package", optional_fields)
            self.assertIn("quantity", optional_fields)
            self.assertNotIn("frequency", optional_fields)
            self.assertFalse(error)

    def test_parse_optional_item_fields_error_quantity(self):
        xml = """
            <Item>
                <ItemPackage>1000 TABLETS</ItemPackage>
                <ItemQuantity>42ml</ItemQuantity>
                <ItemFrequency>2</ItemFrequency>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            code = "ERROR_QTY"
            optional_fields, error = parse_optional_item_fields(root, code)

            self.assertFalse(optional_fields)
            self.assertTrue(error)
            self.assertIn("quantity is invalid", error)
            self.assertIn(code, error)

    def test_parse_optional_item_fields_error_frequency(self):
        xml = """
            <Item>
                <ItemPackage>1000 TABLETS</ItemPackage>
                <ItemFrequency>5.55</ItemFrequency>
                <ItemQuantity>42.00</ItemQuantity>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            code = "ERROR_FRQ"
            optional_fields, error = parse_optional_item_fields(root, code)

            self.assertNotIn("frequency", optional_fields)
            self.assertTrue(error)
            self.assertIn("frequency is invalid", error)
            self.assertIn(code, error)

    def test_parse_optional_item_fields_error_package_too_small(self):
        xml = """
            <Item>
                <ItemPackage> </ItemPackage>
                <ItemFrequency>1</ItemFrequency>
                <ItemQuantity>42.00</ItemQuantity>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            code = "ERROR_PKG"
            optional_fields, error = parse_optional_item_fields(root, code)

            self.assertNotIn("package", optional_fields)
            self.assertTrue(error)
            self.assertIn("package is invalid", error)
            self.assertIn(code, error)

    def test_parse_optional_item_fields_error_package_too_long(self):
        long_boi = "this package is really long, why? Why would anyone prepare a medical item " \
                   "with a packaging so long that it doesn't fit in 255 characters, it doesn't " \
                   "make any sense... and still, i haven't currently reached 255 characters yet, so " \
                   "I am trying to get there and writing anything... please enjoy if you read these tests later :)"
        xml = f"""
            <Item>
                <ItemPackage>{long_boi}</ItemPackage>
                <ItemFrequency>12</ItemFrequency>
                <ItemQuantity>2.00</ItemQuantity>
            </Item>
        """.encode("utf8")
        with TemporaryFile() as tf:
            tf.write(xml)
            tf.seek(0)
            et = ElementTree.parse(tf)
            root = et.getroot()

            code = "ERROR_PKG"
            optional_fields, error = parse_optional_item_fields(root, code)

            self.assertNotIn("package", optional_fields)
            self.assertTrue(error)
            self.assertIn("package is invalid", error)
            self.assertIn(code, error)


class UploadItemsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(username="testItemsAdmin")

    @patch("tools.services.parse_xml_items")
    def test_upload_items_multiple_insert_dry_run(self, mock_parsing):
        dry_run = True
        strategy = STRATEGY_INSERT
        existing_code = "0001"
        raw_items = [
            {
                "code": "CODE_1",
                "name": "Valid item 1 - no error",
            },
            {
                "code": "CODE_2",
                "name": "Valid item 2 - no error",
            },
            {
                "code": existing_code,
                "name": "Invalid item - code already exists",
            }
        ]
        errors = []
        mock_parsing.return_value = raw_items, errors

        expected_errors = [
            f"Item '{existing_code}' already exists"
        ]
        expected = UploadResult(
            errors=expected_errors,
            sent=3,
            created=2,
            updated=0,
            deleted=0,
        )
        result = upload_items(self.admin_user, "xml", strategy, dry_run)

        self.assertEqual(expected, result)

    @patch("tools.services.parse_xml_items")
    def test_upload_items_multiple_update_dry_run(self, mock_parsing):
        dry_run = True
        strategy = STRATEGY_UPDATE
        existing_code_1 = "0001"
        existing_code_2 = "0127"
        error_code = "ERROR"
        raw_items = [
            {
                "code": existing_code_1,
                "name": "Valid item 1 - no error",
            },
            {
                "code": error_code,
                "name": "Invalid item - code doesn't exists",
            },
            {
                "code": existing_code_2,
                "name": "Valid item 2 - no error",
            },
        ]
        errors = []
        mock_parsing.return_value = raw_items, errors

        expected_errors = [
            f"Item '{error_code}' does not exist"
        ]
        expected = UploadResult(
            errors=expected_errors,
            sent=3,
            created=0,
            updated=2,
            deleted=0,
        )
        result = upload_items(self.admin_user, "xml", strategy, dry_run)

        self.assertEqual(expected, result)

    @patch("tools.services.parse_xml_items")
    def test_upload_items_multiple_insert_update_dry_run(self, mock_parsing):
        dry_run = True
        strategy = STRATEGY_INSERT_UPDATE
        raw_items = [
            {
                "code": "CODE_1",
                "name": "New item 1",
            },
            {
                "code": "CODE_2",
                "name": "New item 2",
            },
            {
                "code": "0001",
                "name": "Existing item 1",
            },
            {
                "code": "CODE_3",
                "name": "New item 3",
            },
            {
                "code": "0042",
                "name": "Existing item 2",
            },
        ]
        errors = []
        mock_parsing.return_value = raw_items, errors

        expected = UploadResult(
            errors=errors,
            sent=5,
            created=3,
            updated=2,
            deleted=0,
        )
        result = upload_items(self.admin_user, "xml", strategy, dry_run)

        self.assertEqual(expected, result)

    @patch("tools.services.parse_xml_items")
    def test_upload_items_multiple_insert_update_delete_dry_run(self, mock_parsing):
        dry_run = True
        strategy = STRATEGY_INSERT_UPDATE_DELETE
        raw_items = [
            {
                "code": "CODE_1",
                "name": "New item 1",
            },
            {
                "code": "CODE_2",
                "name": "New item 2",
            },
            {
                "code": "0001",
                "name": "Existing item 1",
            },
            {
                "code": "CODE_3",
                "name": "New item 3",
            },
            {
                "code": "0042",
                "name": "Existing item 2",
            },
        ]
        errors = []
        mock_parsing.return_value = raw_items, errors

        before_total_items = Item.objects.filter(*Item.filter_validity()).count()
        expected_deleted = before_total_items - 2

        expected = UploadResult(
            errors=errors,
            sent=5,
            created=3,
            updated=2,
            deleted=expected_deleted,
        )
        result = upload_items(self.admin_user, "xml", strategy, dry_run)

        self.assertEqual(expected, result)

    @patch("tools.services.parse_xml_items")
    def test_upload_items_multiple_insert(self, mock_parsing):
        # setup - preparing data that will be inserted
        dry_run = False
        strategy = STRATEGY_INSERT
        existing_code = "0001"
        new_code_1 = "CODE_1"
        new_code_2 = "CODE_2"
        raw_items = [
            {
                "code": new_code_1,
                "name": "Valid item 1 - no error",
                "type": "D",
                "price": 489.54,
                "care_type": "O",
                "patient_category": 15,
                "package": "package",
                "frequency": 5,
                "quantity": 1.2,
            },
            {
                "code": new_code_2,
                "name": "Valid item 2 - no error",
                "type": "D",
                "price": 499.54,
                "care_type": "O",
                "patient_category": 5,
                "package": "package",
                "frequency": 57,
                "quantity": 1.27,
            },
            {
                "code": existing_code,
                "name": "Invalid item - code already exists",
                "type": "D",
                "price": 599.54,
                "care_type": "B",
                "patient_category": 7,
                "package": "package",
                "frequency": 7,
                "quantity": 7,
            }
        ]
        errors = []
        mock_parsing.return_value = raw_items, errors

        expected_errors = [
            f"Item '{existing_code}' already exists"
        ]
        expected = UploadResult(
            errors=expected_errors,
            sent=3,
            created=2,
            updated=0,
            deleted=0,
        )
        total_items_before = Item.objects.filter(*Item.filter_validity()).count()

        # Inserting
        result = upload_items(self.admin_user, "xml", strategy, dry_run)
        total_items_after = Item.objects.filter(*Item.filter_validity()).count()

        self.assertEqual(expected, result)
        self.assertEqual(total_items_before + 2, total_items_after)

        # Making sure the new items don't stay in the DB
        new_item_1 = Item.objects.get(code=new_code_1)
        new_item_1.delete()
        new_item_2 = Item.objects.get(code=new_code_2)
        new_item_2.delete()

    @patch("tools.services.parse_xml_items")
    def test_upload_items_multiple_update(self, mock_parsing):
        # setup - creating items that will be updated
        new_code_1 = "CODE_1"
        old_name_1 = "new item old name 0001"
        new_item_1_props = {
            "code": new_code_1,
            "name": old_name_1,
        }
        create_test_item(item_type="D", custom_props=new_item_1_props)

        new_code_2 = "CODE_2"
        old_name_2 = "new item old name 0002"
        new_item_2_props = {
            "code": new_code_2,
            "name": old_name_2,
        }
        create_test_item(item_type="D", custom_props=new_item_2_props)

        # setup - preparing values used for the update
        dry_run = False
        strategy = STRATEGY_UPDATE
        new_name_1 = "new item new name 0001"
        new_name_2 = "new item new name 0002"
        non_existing_code = "ERROR"
        raw_items = [
            {
                "code": new_code_1,
                "name": new_name_1,
                "type": "m",
                "price": 66.54,
                "care_type": "i",
                "patient_category": 15,
                "package": "package",
                "quantity": 7,
            },
            {
                "code": new_code_2,
                "name": new_name_2,
                "type": "m",
                "price": 66.54,
                "care_type": "I",
                "patient_category": 15,
                "package": "package",
                "quantity": 7,
            },
            {
                "code": non_existing_code,
                "name": "error - this can't be updated",
                "type": "m",
                "price": 66.54,
                "care_type": "I",
                "patient_category": 15,
            }
        ]
        errors = []
        mock_parsing.return_value = raw_items, errors
        expected_errors = [
            f"Item '{non_existing_code}' does not exist"
        ]
        expected = UploadResult(
            errors=expected_errors,
            sent=3,
            created=0,
            updated=2,
            deleted=0,
        )
        total_items_before = Item.objects.filter(*Item.filter_validity()).count()

        # update
        result = upload_items(self.admin_user, "xml", strategy, dry_run)
        total_items_after = Item.objects.filter(*Item.filter_validity()).count()

        self.assertEqual(expected, result)
        self.assertEqual(total_items_before, total_items_after)

        # Making sure the names have been updated + deleting the new items to make sure they don't stay in the DB
        db_new_item_1 = Item.objects.get(code=new_code_1, validity_to=None)
        self.assertEqual(db_new_item_1.name, new_name_1)
        db_new_item_1.delete()

        db_new_item_2 = Item.objects.get(code=new_code_2, validity_to=None)
        self.assertEqual(db_new_item_2.name, new_name_2)
        db_new_item_2.delete()

    @patch("tools.services.parse_xml_items")
    def test_upload_items_multiple_insert_update(self, mock_parsing):
        # setup - creating items that will be updated
        update_code_1 = "U_1"
        old_name_1 = "update item old name 0001"
        update_item_1_props = {
            "code": update_code_1,
            "name": old_name_1,
        }
        create_test_item(item_type="D", custom_props=update_item_1_props)

        update_code_2 = "U_2"
        old_name_2 = "update item old name 0002"
        update_item_2_props = {
            "code": update_code_2,
            "name": old_name_2,
        }
        create_test_item(item_type="D", custom_props=update_item_2_props)

        # setup - preparing values used for the update
        dry_run = False
        strategy = STRATEGY_INSERT_UPDATE
        new_name_1 = "update item new name 0001"
        new_name_2 = "update item new name 0002"
        insert_code_1 = "I_1"
        insert_code_2 = "I_2"
        raw_items = [
            {
                "code": insert_code_1,
                "name": "insert item 1",
                "type": "m",
                "price": 65.54,
                "care_type": "b",
                "patient_category": 15,
                "package": "yes",
                "quantity": 7,
            },
            {
                "code": update_code_1,
                "name": new_name_1,
                "type": "m",
                "price": 66.54,
                "care_type": "i",
                "patient_category": 15,
                "package": "package",
                "quantity": 7,
                "frequency": 6,
            },
            {
                "code": update_code_2,
                "name": new_name_2,
                "type": "m",
                "price": 66.54,
                "care_type": "I",
                "patient_category": 15,
            },
            {
                "code": insert_code_2,
                "name": "insert item 2",
                "type": "m",
                "price": 60.54,
                "care_type": "b",
                "patient_category": 15,
                "quantity": 7,
            },
        ]
        errors = []
        mock_parsing.return_value = raw_items, errors
        expected = UploadResult(
            errors=errors,
            sent=4,
            created=2,
            updated=2,
            deleted=0,
        )
        total_items_before = Item.objects.filter(*Item.filter_validity()).count()

        # insert-update
        result = upload_items(self.admin_user, "xml", strategy, dry_run)
        total_items_after = Item.objects.filter(*Item.filter_validity()).count()

        self.assertEqual(expected, result)
        self.assertEqual(total_items_before + 2, total_items_after)

        # Making sure the names have been updated + deleting the update items to make sure they don't stay in the DB
        db_update_item_1 = Item.objects.get(code=update_code_1, validity_to=None)
        self.assertEqual(db_update_item_1.name, new_name_1)
        db_update_item_1.delete()

        db_update_item_2 = Item.objects.get(code=update_code_2, validity_to=None)
        self.assertEqual(db_update_item_2.name, new_name_2)
        db_update_item_2.delete()

        # Also deleting the insert items to make sure they don't stay in the DB
        db_insert_item_1 = Item.objects.get(code=insert_code_1, validity_to=None)
        db_insert_item_1.delete()
        db_insert_item_2 = Item.objects.get(code=insert_code_2, validity_to=None)
        db_insert_item_2.delete()

    @patch("tools.services.parse_xml_items")
    def test_upload_items_multiple_insert_update_delete(self, mock_parsing):
        # setup - fetching initial DB items in order not to delete them
        all_items = Item.objects.filter(*Item.filter_validity()).all()
        items_to_not_delete = []
        for item in all_items:
            item_dict = item.__dict__
            item_dict.pop("id")
            item_dict.pop("uuid")
            item_dict.pop("_state")
            item_dict.pop("validity_from")
            item_dict.pop("validity_to")
            item_dict.pop("legacy_id")
            items_to_not_delete.append(item_dict)

        # setup - creating items that will be updated & deleted
        update_code = "U_1"
        old_name = "update item old name 0001"
        update_item_props = {
            "code": update_code,
            "name": old_name,
        }
        create_test_item(item_type="D", custom_props=update_item_props)

        delete_code = "D_1"
        delete_item_props = {
            "code": delete_code,
            "name": "item do be deleted",
        }
        create_test_item(item_type="D", custom_props=delete_item_props)

        # setup - preparing values used for the tests
        dry_run = False
        strategy = STRATEGY_INSERT_UPDATE_DELETE
        update_new_name = "update item new name 0001"
        insert_code_1 = "I_1"
        insert_code_2 = "I_2"
        new_items = [
            {
                "code": insert_code_1,
                "name": "insert item 1",
                "type": "m",
                "price": 65.54,
                "care_type": "b",
                "patient_category": 15,
                "package": "yes",
                "quantity": 7,
            },
            {
                "code": update_code,
                "name": update_new_name,
                "type": "m",
                "price": 66.54,
                "care_type": "i",
                "patient_category": 15,
                "package": "package",
                "quantity": 7,
                "frequency": 6,
            },
            {
                "code": insert_code_2,
                "name": "insert item 2",
                "type": "m",
                "price": 60.54,
                "care_type": "b",
                "patient_category": 15,
                "quantity": 7,
            },
        ]
        raw_items = new_items + items_to_not_delete
        errors = []
        mock_parsing.return_value = raw_items, errors

        total_updated = len(items_to_not_delete) + 1
        total_sent = total_updated + 2
        expected = UploadResult(
            errors=errors,
            sent=total_sent,
            created=2,
            updated=total_updated,
            deleted=1,
        )
        total_items_before = Item.objects.filter(*Item.filter_validity()).count()

        # insert update delete
        result = upload_items(self.admin_user, "xml", strategy, dry_run)
        total_items_after = Item.objects.filter(*Item.filter_validity()).count()

        self.assertEqual(expected, result)
        # 2 inserts and 1 deletion
        self.assertEqual(total_items_before + 1, total_items_after)

        with self.assertRaises(ObjectDoesNotExist):
            Item.objects.get(code=delete_code, validity_to=None)

        # Making sure the name has been updated + deleting the items to make sure they don't stay in the DB
        db_update_item = Item.objects.get(code=update_code, validity_to=None)
        self.assertEqual(db_update_item.name, update_new_name)
        db_update_item.delete()

        db_insert_item_1 = Item.objects.get(code=insert_code_1, validity_to=None)
        db_insert_item_1.delete()
        db_insert_item_2 = Item.objects.get(code=insert_code_2, validity_to=None)
        db_insert_item_2.delete()
