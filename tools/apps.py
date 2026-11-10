from django.apps import AppConfig
from django.conf import settings

from core.rights_declaration import RightsDeclaration

MODULE_NAME = "tools"

# Rights, by entity then by action.
#
# What is particular to `tools`: each of its eleven `_perms` keys is a **stack** of
# several identifiers, evaluated as an OR by `has_perms`. The stack dates from the
# initial commit (November 2021) and reproduces the historical IMIS catalogue; it is
# kept as it stands here. The declaration breaks it down - one identifier = one named
# action - so that the stack becomes readable, but the lists laid on the config class
# stay identical byte for byte: no role loses an access.
#
# Two consequences to keep in mind, not fixed in this batch of work:
#   * `views.py` guards a register's `GET download_*` and `POST upload_*` with the
#     **same** key. Declaring `query` and `write` separately names the split without
#     making it: as long as the key stacks both identifiers, reading a register gives
#     the right to rewrite it (the `INSERT_UPDATE_DELETE` strategy included).
#   * `permissions_map.json` catalogues only one identifier per key because its
#     generator overwrites the value on every pass of the loop
#     (`generate_permissions_map.py` ~l.38:
#     `for perm_id in perm_ids: permissions_map[key] = perm_id`) - the **last** one
#     wins. The seven identifiers missing from the map (131000, 131002, 131004, 131006,
#     131008, 131010, 131102) are therefore not dead identifiers: they are
#     inexpressible by a map with one identifier per key. The frontend even requires
#     them explicitly (`ToolsModule/src/constants.js`, evaluated as an AND by
#     `hasRights`), so deployments do grant them.
DJANGO_PERMS = {
    # The registers' "cross-cutting" right. 131000 is stacked at the head of the six
    # `registers_*` keys: holding it is enough for any register at all. It is declared
    # here once rather than repeated on each entity, which avoids six declarations of
    # the same integer that could no longer be told apart from a copy-paste.
    # 131100 is the catalogue right (`tools.registers`), carried by `registers_perms`,
    # which no view reads any more - a dormant declaration, see _PERM_CFG.
    "registers": {
        "any": ("tools.view_any_register", 131000),
        "query": ("tools.view_registers", 131100),
    },
    # A register = a file exchange over reference data owned by another module
    # (medical, location). The actions:
    #   `query` = the `GET registers/download_*`, odd identifier, the only catalogued
    #   one;
    #   `write` = the `POST registers/upload_*`, even identifier.
    # `write` and not `create`/`update`/`delete`: the strategy (`INSERT`, `UPDATE`,
    # `INSERT_UPDATE`, `INSERT_UPDATE_DELETE`) is a parameter of the request and not a
    # distinct route, so a single identifier covers all three canonical verbs.
    # The openIMIS numbering of the 1310xx block is what grounds the odd/even reading:
    # 00 section, 01/02 diagnoses, 03/04 health facilities, 05/06 locations, 07/08
    # items, 09/10 services - the same `<block>1 = search, <block>2 = write` as
    # everywhere else (see insuree 101001..101004).
    "registersDiagnoses": {
        "query": ("tools.view_registersdiagnoses", 131001),
        "write": ("tools.write_registersdiagnoses", 131002),
    },
    "registersHealthFacilities": {
        "query": ("tools.view_registershealthfacilities", 131003),
        "write": ("tools.write_registershealthfacilities", 131004),
    },
    "registersLocations": {
        "query": ("tools.view_registerslocations", 131005),
        "write": ("tools.write_registerslocations", 131006),
    },
    "registersItems": {
        "query": ("tools.view_registersitems", 131007),
        "write": ("tools.write_registersitems", 131008),
    },
    "registersServices": {
        "query": ("tools.view_registersservices", 131009),
        "write": ("tools.write_registersservices", 131010),
    },
    # Exports. Each is a read: a `GET extracts/download_*` route that builds an
    # archive. None has a write counterpart.
    "masterDataExtract": {
        "query": ("tools.view_masterdataextract", 131101),
    },
    "phoneExtract": {
        "query": ("tools.view_phoneextract", 131103),
        # 131102 has been stacked ahead of 131103 from the start and is catalogued
        # nowhere. Nothing in this repository says what it denoted in the historical
        # IMIS - unlike the registers, the 1311xx block numbers one function per
        # identifier and not read/write pairs. It is kept, with no invented business
        # name, because removing it would amount to revoking the phone export from the
        # roles that carry only it.
        "queryAlt": ("tools.view_phoneextract_alt", 131102),
    },
    "officerRenewalsExtract": {
        "query": ("tools.view_officerrenewalsextract", 131105),
    },
    "officerFeedbacksExtract": {
        "query": ("tools.view_officerfeedbacksextract", 131106),
    },
    # Upload of offline reimbursement claims. `create`: the route creates claims, it
    # neither reads nor modifies any.
    "claimsUpload": {
        "create": ("tools.add_claimsupload", 131104),
    },
}

# A config key points at the **main** action of its stack - the one whose identifier is
# catalogued. The stacked actions (`registers.any`, `registers*.write`,
# `phoneExtract.queryAlt`) deliberately have no key of their own: they are not
# separately checkable today, since the single key governs both the download and the
# upload. `configured(entity, action)` therefore returns None for them, and a caller
# querying them fails closed instead of receiving the whole stack while believing it
# holds the write right alone.
_PERM_CFG = {
    # Dormant: no view reads `registers_perms`; only `core.test_helpers` grants it, in
    # two test roles. Kept as it stands - removing it would take 131100 out of the
    # catalogue of grantable rights.
    "registers_perms": ("registers", "query"),
    "registers_diagnoses_perms": ("registersDiagnoses", "query"),
    "registers_health_facilities_perms": ("registersHealthFacilities", "query"),
    "registers_locations_perms": ("registersLocations", "query"),
    "registers_items_perms": ("registersItems", "query"),
    "registers_services_perms": ("registersServices", "query"),
    "extracts_master_data_perms": ("masterDataExtract", "query"),
    "extracts_officer_feedbacks_perms": ("officerFeedbacksExtract", "query"),
    "extracts_officer_renewals_perms": ("officerRenewalsExtract", "query"),
    "extracts_phone_extract_perms": ("phoneExtract", "query"),
    "extracts_upload_claims_perms": ("claimsUpload", "create"),
}

RIGHTS = RightsDeclaration(MODULE_NAME, DJANGO_PERMS, _PERM_CFG)

perms = RIGHTS.perms
django_perms = RIGHTS.django_perm_names
configured_perms = RIGHTS.configured
require = RIGHTS.require


DEFAULT_CFG = {
    "master_data_password": None,
}


class ToolsConfig(AppConfig):
    name = MODULE_NAME

    # Rights: constants derived from DJANGO_PERMS, no longer overridable. They go
    # neither through DEFAULT_CFG nor through ready():
    # `ModuleConfiguration.get_or_default` now ignores any `_perms` key stored in the
    # database.
    #
    # The stacks are rebuilt in their exact original order: `has_perms` does an OR, so
    # the order has no effect at runtime, but keeping it makes the conversion
    # verifiable by strict equality (see tests/test_permission_declarations.py).
    registers_perms = RIGHTS.perms("registers", "any", "query")
    registers_diagnoses_perms = RIGHTS.perms("registers", "any") + RIGHTS.perms(
        "registersDiagnoses", "write", "query"
    )
    registers_health_facilities_perms = RIGHTS.perms("registers", "any") + RIGHTS.perms(
        "registersHealthFacilities", "write", "query"
    )
    registers_locations_perms = RIGHTS.perms("registers", "any") + RIGHTS.perms(
        "registersLocations", "write", "query"
    )
    registers_items_perms = RIGHTS.perms("registers", "any") + RIGHTS.perms(
        "registersItems", "write", "query"
    )
    registers_services_perms = RIGHTS.perms("registers", "any") + RIGHTS.perms(
        "registersServices", "write", "query"
    )

    extracts_master_data_perms = RIGHTS.perms("masterDataExtract", "query")
    extracts_officer_feedbacks_perms = RIGHTS.perms("officerFeedbacksExtract", "query")
    extracts_officer_renewals_perms = RIGHTS.perms("officerRenewalsExtract", "query")
    extracts_phone_extract_perms = RIGHTS.perms("phoneExtract", "queryAlt", "query")
    extracts_upload_claims_perms = RIGHTS.perms("claimsUpload", "create")

    master_data_password = None

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(ToolsConfig, field):
                setattr(ToolsConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)

    @classmethod
    def get_master_data_password(cls):
        return cls.master_data_password or (
            hasattr(settings, "MASTER_DATA_PASSWORD") and settings.MASTER_DATA_PASSWORD
        )
