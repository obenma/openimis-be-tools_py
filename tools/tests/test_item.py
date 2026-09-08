import os
from tablib import Dataset
from core.test_helpers import create_test_interactive_user
from django.test import TestCase
from medical.test_helpers import create_test_item
from tools.resources import ItemResource


class ImportItemTest(TestCase):

    def setUp(self) -> None:
        super(ImportItemTest, self).setUp()
        self.user = create_test_interactive_user()
        create_test_item('S', custom_props={"code": 'SS'})

    def test_simple_import(self):
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        resource = ItemResource(user=self.user)
        dataset = Dataset()
        with open(os.path.join(dir_path, 'tests/item_example.json'), 'r') as f:
            dataset.load(f.read())
            result = resource.import_data(
                dataset, dry_run=True, use_transactions=True,
                collect_failed_rows=False,
            )
            self.assertEqual(result.has_errors(), False)

    def test_simple_export(self):
        result = ItemResource(self.user).export().dict
        self.assertTrue(result)
