import dagster as dg

defs = dg.Definitions(
    sensors=[
        dg.AutomationConditionSensorDefinition(
            "team_b_sensor", target=dg.AssetSelection.groups("team_a")
        ),
        dg.AutomationConditionSensorDefinition(
            "team_a_sensor", target=dg.AssetSelection.groups("team_b")
        ),
    ],
)
