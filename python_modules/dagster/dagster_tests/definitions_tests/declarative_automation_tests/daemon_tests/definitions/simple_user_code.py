import dagster as dg


def get_defs() -> dg.Definitions:
    from .simple_defs import defs as simple_defs  # noqa

    return dg.Definitions(
        assets=simple_defs.assets,
        sensors=[
            dg.AutomationConditionSensorDefinition(
                name="the_sensor", target="*", use_user_code_server=True
            )
        ],
    )


defs = get_defs()
