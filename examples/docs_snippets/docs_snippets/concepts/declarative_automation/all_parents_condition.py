import dagster as dg


def get_condition(asset_key) -> dg.AutomationCondition:
    asset_key_handled = dg.AutomationCondition.asset_matches(
        asset_key,
        dg.AutomationCondition.newly_requested()
        | dg.AutomationCondition.newly_updated(),
    )
    return dg.AutomationCondition.all_deps_match(
        dg.AutomationCondition.newly_updated().since(asset_key_handled)
    )


@dg.asset(automation_condition=get_condition("downstream_asset"), deps=["a", "b"])
def downstream_asset() -> None: ...
