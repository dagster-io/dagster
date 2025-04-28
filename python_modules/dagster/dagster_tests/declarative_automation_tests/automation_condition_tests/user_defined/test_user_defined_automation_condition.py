import logging

from dagster import (
    AutomationCondition,
    AutomationContext,
    AutomationResult,
    DagsterInstance,
    asset,
    evaluate_automation_conditions,
)


def test_cursoring() -> None:
    class MyAutomationCondition(AutomationCondition):
        def evaluate(self, context: AutomationContext) -> AutomationResult:
            if context.cursor == "hi":
                cursor = None
                true_subset = context.candidate_subset
            else:
                cursor = "hi"
                true_subset = context.get_empty_subset()

            return AutomationResult(context, true_subset=true_subset, cursor=cursor)

    @asset(automation_condition=MyAutomationCondition())
    def my_asset() -> None: ...

    instance = DagsterInstance.ephemeral()
    cursor = None

    for i in range(5):
        result = evaluate_automation_conditions(defs=[my_asset], instance=instance, cursor=cursor)
        cursor = result.cursor

        # should toggle between returning 0 and 1 every evaluation
        if i % 2 == 0:
            assert result.get_num_requested(my_asset.key) == 0
        else:
            assert result.get_num_requested(my_asset.key) == 1


def test_logging(caplog) -> None:
    class MyAutomationCondition(AutomationCondition):
        def evaluate(self, context: AutomationContext) -> AutomationResult:
            context.log.debug("DEBUG_THING")
            context.log.info("INFO_THING")

            return AutomationResult(context, true_subset=context.get_empty_subset())

    @asset(automation_condition=MyAutomationCondition())
    def my_asset() -> None: ...

    caplog.set_level(logging.INFO)
    evaluate_automation_conditions(defs=[my_asset], instance=DagsterInstance.ephemeral())

    assert "INFO_THING" in caplog.text
    assert "DEBUG_THING" not in caplog.text
    assert "MyAutomationCondition" in caplog.text

    caplog.set_level(logging.DEBUG)
    evaluate_automation_conditions(defs=[my_asset], instance=DagsterInstance.ephemeral())
    assert "DEBUG_THING" in caplog.text
