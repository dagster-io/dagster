import dagster as dg


@dg.asset
def raw_files() -> None: ...


# `processed_files` lives in this code location. Its only check (`external_non_null`) is
# defined in a *different* code location (`cross_location_unconditioned_check.py`), so this
# location's implicit asset job does not contain that check.
@dg.asset(automation_condition=dg.AutomationCondition.eager(), deps=[raw_files])
def processed_files() -> None: ...


defs = dg.Definitions(assets=[raw_files, processed_files])
