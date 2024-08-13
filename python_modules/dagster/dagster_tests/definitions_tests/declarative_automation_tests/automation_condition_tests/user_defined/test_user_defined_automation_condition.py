from dagster import AutomationCondition, DagsterInstance, asset, evaluate_automation_conditions
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext


def test_cursoring() -> None:
    class MyAutomationCondition(AutomationCondition):
        def evaluate(self, context: AutomationContext) -> AutomationResult:
            if context.cursor == "hi":
                cursor = None
                true_slice = context.candidate_slice
            else:
                cursor = "hi"
                true_slice = context.get_empty_slice()

            return AutomationResult(context, true_slice=true_slice, cursor=cursor)

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
