import dagster as dg


@dg.asset(automation_condition=dg.AutomationCondition.eager())
def thing() -> None: ...


@dg.asset()
def other_thing() -> None: ...


defs = dg.Definitions(
    assets=[thing, other_thing],
    sensors=[
        dg.AutomationConditionSensorDefinition(
            name="all_assets_non_user_space",
            asset_selection=dg.AssetSelection.all(),
            user_code=False,
        )
    ],
)
