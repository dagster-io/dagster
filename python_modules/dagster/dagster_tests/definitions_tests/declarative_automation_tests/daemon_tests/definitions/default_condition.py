import dagster as dg


@dg.asset(automation_condition=dg.AutomationCondition.missing().newly_true())
def eager_asset() -> None: ...


@dg.asset()
def every_5_minutes_asset() -> None: ...


defs = dg.Definitions(
    assets=[eager_asset, every_5_minutes_asset],
    sensors=[
        dg.AutomationConditionSensorDefinition(
            name="all_assets",
            asset_selection=dg.AssetSelection.all(),
            default_condition=dg.AutomationCondition.cron_tick_passed("*/5 * * * *"),
            use_user_code_server=True,
        )
    ],
)
