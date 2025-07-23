import logging

import dagster as dg
from dagster import AutomationContext, DagsterInstance


def test_cursoring() -> None:
    class MyAutomationCondition(dg.AutomationCondition):
        def evaluate(self, context: AutomationContext) -> dg.AutomationResult:
            if context.cursor == "hi":
                cursor = None
                true_subset = context.candidate_subset
            else:
                cursor = "hi"
                true_subset = context.get_empty_subset()

            return dg.AutomationResult(context, true_subset=true_subset, cursor=cursor)

    @dg.asset(automation_condition=MyAutomationCondition())
    def my_asset() -> None: ...

    instance = DagsterInstance.ephemeral()
    cursor = None

    for i in range(5):
        result = dg.evaluate_automation_conditions(
            defs=[my_asset], instance=instance, cursor=cursor
        )
        cursor = result.cursor

        # should toggle between returning 0 and 1 every evaluation
        if i % 2 == 0:
            assert result.get_num_requested(my_asset.key) == 0
        else:
            assert result.get_num_requested(my_asset.key) == 1


def test_logging(caplog) -> None:
    class MyAutomationCondition(dg.AutomationCondition):
        def evaluate(self, context: AutomationContext) -> dg.AutomationResult:
            context.log.debug("DEBUG_THING")
            context.log.info("INFO_THING")

            return dg.AutomationResult(context, true_subset=context.get_empty_subset())

    @dg.asset(automation_condition=MyAutomationCondition())
    def my_asset() -> None: ...

    caplog.set_level(logging.INFO)
    dg.evaluate_automation_conditions(defs=[my_asset], instance=DagsterInstance.ephemeral())

    assert "INFO_THING" in caplog.text
    assert "DEBUG_THING" not in caplog.text
    assert "MyAutomationCondition" in caplog.text

    caplog.set_level(logging.DEBUG)
    dg.evaluate_automation_conditions(defs=[my_asset], instance=DagsterInstance.ephemeral())
    assert "DEBUG_THING" in caplog.text
