import dagster as dg


def get_defs() -> dg.Definitions:
    from .backfill_simple_user_code import defs as uc_defs  # noqa

    return dg.Definitions(
        assets=uc_defs.assets,
        sensors=[dg.AutomationConditionSensorDefinition(name="the_sensor", asset_selection="*")],
    )


defs = get_defs()
