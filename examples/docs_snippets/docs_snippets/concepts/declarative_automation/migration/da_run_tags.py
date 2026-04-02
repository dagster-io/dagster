import dagster as dg

automation_sensor = dg.AutomationConditionSensorDefinition(
    "my_automation_sensor",
    target=dg.AssetSelection.all(),
    default_status=dg.DefaultSensorStatus.RUNNING,
    run_tags={"team": "data-eng", "source": "automation"},
)
