"""
Guard rails on tools' rights declaration.

Same structure as `claim` and `product`: `DJANGO_PERMS` by entity then by action,
`_PERM_CFG` linking the config keys, and `Extract.get_rights` as the access point.

What makes `tools` different, and is the reason half this file exists: its eleven
config keys carry not one identifier but a **stack** of several, evaluated as an OR by
`has_perms`. The stack dates from the initial commit and reproduces the historical IMIS
catalogue. What is locked down here:

  * the exact value of each stack, order included - that is what makes visible in
    review any conversion that would "tidy up" an identifier and, in the same stroke,
    withdraw access from the roles that carry only that one;
  * the list of actions deliberately absent from `_PERM_CFG`: the stacked alternates
    are not separately checkable today, and adding an action without thinking about it
    has to make this test fail;
  * the fact that `configured()` returns None on those alternates, so that the caller
    fails closed rather than receiving the whole stack while believing it holds the
    write right alone.

What this file does **not** lock down, for want of a decision: the read/write split of
the registers. `views.py` guards the `GET download_*` and the `POST upload_*` with the
same key; the `query` and `write` actions are declared separately but stacked in the
same key, so the split is named, not made.
"""

import json
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from tools.apps import (
    DJANGO_PERMS,
    ToolsConfig,
    _PERM_CFG,
    configured_perms,
    django_perms,
    perms,
)
from tools.models import Extract

# The stacks as deployed, order included. Changing one is incompatible with the
# existing roles: this test has to be updated *and* the new right granted.
EXPECTED_RIGHTS = {
    "registers_perms": ["131000", "131100"],
    "registers_diagnoses_perms": ["131000", "131002", "131001"],
    "registers_health_facilities_perms": ["131000", "131004", "131003"],
    "registers_locations_perms": ["131000", "131006", "131005"],
    "registers_items_perms": ["131000", "131008", "131007"],
    "registers_services_perms": ["131000", "131010", "131009"],
    "extracts_master_data_perms": ["131101"],
    "extracts_officer_feedbacks_perms": ["131106"],
    "extracts_officer_renewals_perms": ["131105"],
    "extracts_phone_extract_perms": ["131102", "131103"],
    "extracts_upload_claims_perms": ["131104"],
}

# What `permissions_map.json` catalogues for tools. A single identifier per key:
# `generate_permissions_map.py` overwrites the value on every pass of the loop, so it
# is the **last** of the stack that comes out. The others are not dead, they are
# inexpressible by a map with one identifier per key.
CATALOGUED = {
    "tools.registers": "131100",
    "tools.registers_diagnoses": "131001",
    "tools.registers_health_facilities": "131003",
    "tools.registers_locations": "131005",
    "tools.registers_items": "131007",
    "tools.registers_services": "131009",
    "tools.extracts_master_data": "131101",
    "tools.extracts_officer_feedbacks": "131106",
    "tools.extracts_officer_renewals": "131105",
    "tools.extracts_phone_extract": "131103",
    "tools.extracts_upload_claims": "131104",
}

# Stacked identifiers that no entry of the map names. Taken from
# `core.tests.test_permission_map_consistency.KNOWN_UNCATALOGUED`, pinned here so that
# the list does not grow silently.
UNCATALOGUED = {"131000", "131002", "131004", "131006", "131008", "131010", "131102"}

# Actions declared with no config key of their own: the stacked links of a stack whose
# key is carried by the main action. None of them is separately checkable today.
STACKED_ALTERNATES = {
    ("registers", "any"),
    ("registersDiagnoses", "write"),
    ("registersHealthFacilities", "write"),
    ("registersLocations", "write"),
    ("registersItems", "write"),
    ("registersServices", "write"),
    ("phoneExtract", "queryAlt"),
}


class ToolsPermissionDeclarationTestCase(TestCase):
    def test_right_ids_unchanged(self):
        """The conversion must take nothing out of a stack - not even the order."""
        self.assertEqual(
            {key: getattr(ToolsConfig, key) for key in EXPECTED_RIGHTS}, EXPECTED_RIGHTS
        )

    def test_perm_cfg_points_at_declared_actions_only(self):
        declared = {
            (entity, action)
            for entity, actions in DJANGO_PERMS.items()
            for action in actions
        }
        self.assertEqual(set(_PERM_CFG.values()) - declared, set())

    def test_actions_without_a_config_key_are_only_the_stacked_alternates(self):
        declared = {
            (entity, action)
            for entity, actions in DJANGO_PERMS.items()
            for action in actions
        }
        self.assertEqual(declared - set(_PERM_CFG.values()), STACKED_ALTERNATES)

    def test_perm_cfg_matches_config_attributes(self):
        """`__load_config` ignores the keys with no class attribute."""
        missing = [key for key in _PERM_CFG if not hasattr(ToolsConfig, key)]
        self.assertEqual(missing, [])

    def test_no_right_list_is_empty(self):
        """`has_perms([])` returns True: an empty stack would grant to everybody."""
        empty = [key for key in _PERM_CFG if not getattr(ToolsConfig, key)]
        self.assertEqual(empty, [])

    def test_every_declared_id_is_used_by_a_config_key(self):
        """No declared identifier may stay outside the stacks laid down."""
        declared_ids = {
            str(right_id)
            for actions in DJANGO_PERMS.values()
            for _, right_id in actions.values()
        }
        used = {rid for key in _PERM_CFG for rid in getattr(ToolsConfig, key)}
        self.assertEqual(declared_ids, used)

    def test_catalogued_ids_are_the_last_of_their_stack(self):
        """
        Each key catalogues its main action's identifier, and that is also the last of
        the stack - what the map generator mechanically produces.
        """
        for key, expected in EXPECTED_RIGHTS.items():
            entity, action = _PERM_CFG[key]
            with self.subTest(key=key):
                self.assertEqual(perms(entity, action), [expected[-1]])

    def test_catalogue_matches_permissions_map(self):
        """
        The assembly's catalogue, not the package's: the modules are installed from
        another tree, so it is resolved from BASE_DIR.
        """
        path = Path(settings.BASE_DIR) / "permissions_map.json"
        if not path.exists():  # pragma: no cover - assembly without a map
            self.skipTest(f"{path} absent")
        catalogue = json.loads(path.read_text(encoding="utf-8"))
        actual = {
            key: str(value)
            for key, value in catalogue.items()
            if key.startswith("tools.")
        }
        self.assertEqual(actual, CATALOGUED)

    def test_uncatalogued_ids_are_exactly_the_stacked_alternates(self):
        catalogued = set(CATALOGUED.values())
        declared_ids = {
            str(right_id)
            for actions in DJANGO_PERMS.values()
            for _, right_id in actions.values()
        }
        self.assertEqual(declared_ids - catalogued, UNCATALOGUED)

    def test_stacked_alternates_carry_the_uncatalogued_ids(self):
        self.assertEqual(
            {perms(entity, action)[0] for entity, action in STACKED_ALTERNATES},
            UNCATALOGUED,
        )

    def test_no_right_id_is_shared(self):
        """
        Unlike claim or insuree, tools has no deliberate alias: each identifier is
        declared once and once only. 131000 in particular is factored onto the
        `registers` entity rather than repeated on the five registers.
        """
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (_, right_id) in actions.items():
                seen.setdefault(right_id, []).append(f"{entity}.{action}")
        shared = {rid: who for rid, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_are_unique(self):
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                seen.setdefault(name, []).append(f"{entity}.{action}")
        shared = {name: who for name, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_unknown_entity_or_action_raises(self):
        with self.assertRaises(KeyError):
            perms("nosuchentity", "query")
        with self.assertRaises(KeyError):
            perms("registersItems", "nosuchaction")
        with self.assertRaises(KeyError):
            django_perms("registersItems", "nosuchaction")

    # --- the access point through the model -------------------------------
    def test_extract_exposes_the_phone_extract_read(self):
        self.assertEqual(
            Extract.get_rights("query"), configured_perms("phoneExtract", "query")
        )
        self.assertEqual(Extract.get_rights("query"), EXPECTED_RIGHTS["extracts_phone_extract_perms"])

    def test_stacked_alternate_has_no_configured_value(self):
        """None means "no rule": the caller must fail closed."""
        self.assertIsNone(Extract.get_rights("queryAlt"))
        self.assertIsNone(Extract.get_rights("nosuchaction"))
        for entity, action in STACKED_ALTERNATES:
            with self.subTest(entity=entity, action=action):
                self.assertIsNone(configured_perms(entity, action))

    def test_model_reads_the_configured_value_not_the_declared_default(self):
        """
        ModuleConfiguration may override a right; the check must read the configured
        value, where `perms()` returns the declared default.
        """
        original = ToolsConfig.extracts_phone_extract_perms
        try:
            ToolsConfig.extracts_phone_extract_perms = ["999999"]
            self.assertEqual(Extract.get_rights("query"), ["999999"])
            self.assertEqual(perms("phoneExtract", "query"), ["131103"])
        finally:
            ToolsConfig.extracts_phone_extract_perms = original
