"""
Tests for backend/features/mobile-apps.feature, tools module part (mobile master data).
"""
import os
from unittest import mock

from django.test import TestCase

from core.test_helpers import create_test_interactive_user
from product.test_helpers import create_test_product
from tools import services
from tools.services import create_master_data_export


class MasterDataExportTest(TestCase):
    # Scenario: The master data download works on PostgreSQL (@redmine-34708)
    def test_master_data_export_runs(self):
        product = create_test_product("FMOBMD", custom_props={"age_minimal": 6, "age_maximal": 46})
        user = create_test_interactive_user(username="featmobmd")
        with mock.patch.object(services.json, "dumps", wraps=services.json.dumps) as dumps:  # tools uses simplejson (Decimal-aware)
            result = create_master_data_export(user)
        self.addCleanup(lambda: os.path.exists(result.name) and os.remove(result.name))
        data = dumps.call_args[0][0]
        rows = [{k.lower(): v for k, v in row.items()} for row in data["products"]]
        row = next(r for r in rows if r["productcode"] == product.code)
        self.assertEqual((row["minage"], row["maxage"]), (6, 46))
