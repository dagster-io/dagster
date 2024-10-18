import dagster as dg


class MyCondition(dg.AutomationCondition):
    def evaluate(self, context: dg.AutomationContext) -> dg.AutomationResult:
        # kick off on the 5th evaluation
        if len(context.cursor or "") == 4:
            true_subset = context.candidate_subset
        else:
            true_subset = context.get_empty_subset()

        return dg.AutomationResult(
            context, true_subset=true_subset, cursor=(context.cursor or "") + "."
        )


@dg.asset(automation_condition=MyCondition().since_last_handled())
def foo() -> None: ...


defs = dg.Definitions(
    assets=[foo],
    sensors=[
        dg.AutomationConditionSensorDefinition("the_sensor", asset_selection="*", user_code=True)
    ],
)
