import dagster as dg


def get_defs() -> dg.Definitions:
    from .simple_defs import defs as simple_defs  # noqa

    return dg.Definitions(
        assets=simple_defs.assets,
        sensors=[
            dg.AutomationConditionSensorDefinition(
                name="the_sensor", asset_selection="*", user_code=True
            )
        ],
    )


defs = get_defs()
