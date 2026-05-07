import dagster as dg


@dg.asset(automation_condition=dg.AutomationCondition.eager())
def my_asset(): ...


def test_missing_asset():
    instance = dg.DagsterInstance.ephemeral()

    result = dg.evaluate_automation_conditions(defs=[my_asset], instance=instance)
    assert result.total_requested == 1

    result = dg.evaluate_automation_conditions(
        defs=[my_asset], instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 0
