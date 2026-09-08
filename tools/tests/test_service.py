import os
from tablib import Dataset
from core.test_helpers import create_test_interactive_user
from django.test import TestCase
from tools.resources import ServiceResource
from medical.test_helpers import create_test_service


class ImportServiceTest(TestCase):

    def setUp(self) -> None:
        super(ImportServiceTest, self).setUp()
        self.user = create_test_interactive_user()
        create_test_service('S', custom_props={"code": 'SS'})

    def test_simple_import(self):
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        resource = ServiceResource(user=self.user)
        dataset = Dataset()

        with open(os.path.join(dir_path, 'tests/service_example.json'), 'r') as f:
            dataset.load(f.read())
            result = resource.import_data(
                dataset, dry_run=True, use_transactions=True,
                collect_failed_rows=False,
            )
            self.assertEqual(result.has_errors(), False)

    def test_simple_export(self):
        result = ServiceResource(self.user).export().dict
        self.assertTrue(result)
