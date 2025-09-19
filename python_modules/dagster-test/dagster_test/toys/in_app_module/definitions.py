import dagster as dg

"""
add to local cloud dev with

location_name: in_app_checks
code_source:
  module_name: dagster_test.toys.in_app_module.definitions

Shows the checks as on the always_materializes asset, but i can't run the asset because the
checks are in a different code location
"""


def check_factory(name: str):
    @dg.asset_check(asset="always_materializes", name=name)
    def check_fn():
        return dg.AssetCheckResult(passed=True, asset_key="always_materializes", check_name=name)

    return check_fn


defs = dg.Definitions(asset_checks=[check_factory("first_check"), check_factory("second_check")])
