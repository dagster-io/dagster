import dagster as dg


@dg.asset
def upstream(): ...


@dg.asset(deps=[upstream], automation_condition=dg.AutomationCondition.eager())
def downstream(): ...


def test_eager_condition():
    instance = dg.DagsterInstance.ephemeral()

    result = dg.evaluate_automation_conditions(
        defs=[upstream, downstream], instance=instance
    )
    assert result.total_requested == 0

    dg.materialize([upstream], instance=instance)

    result = dg.evaluate_automation_conditions(
        defs=[upstream, downstream], instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 1
