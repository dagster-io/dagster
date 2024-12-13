import dagster as dg


@dg.asset(automation_condition=dg.AutomationCondition.missing().newly_true())
def eager_asset() -> None: ...


@dg.asset
def default() -> None: ...


@dg.asset(group_name="g1", deps=[default])
def g1_rootA() -> None: ...


@dg.asset(group_name="g1", deps=[default])
def g1_rootB() -> None: ...


@dg.asset(group_name="g1", deps=[g1_rootA, g1_rootB])
def g1_child() -> None: ...


defs = dg.Definitions(
    assets=[default, g1_rootA, g1_rootB, g1_child],
    sensors=[
        dg.AutomationConditionSensorDefinition(
            name="all_assets",
            target=dg.AssetSelection.groups("g1"),
            global_condition=dg.AutomationCondition.all_assets_match(
                selection=dg.AssetSelection.groups("g1").roots(),
                condition=dg.AutomationCondition.eager(),
            ),
            use_user_code_server=True,
        )
    ],
)
