import dagster as dg


@dg.definitions
def sensors():
    return dg.Definitions(
        sensors=[
            dg.AutomationConditionSensorDefinition(
                "run_tags_automation_condition_sensor",
                target=dg.AssetSelection.all(),
                run_tags={"key": "value"},
            )
        ],
    )
