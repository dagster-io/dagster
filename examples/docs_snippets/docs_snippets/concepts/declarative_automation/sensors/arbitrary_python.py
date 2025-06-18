import dagster as dg


@dg.definitions
def sensors():
    return dg.Definitions(
        sensors=[
            dg.AutomationConditionSensorDefinition(
                "automation_condition_sensor",
                target=dg.AssetSelection.all(),
                use_user_code_server=True,
            )
        ]
    )
