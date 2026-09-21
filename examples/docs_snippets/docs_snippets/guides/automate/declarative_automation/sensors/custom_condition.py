def is_company_holiday(foo) -> bool: ...  # ty: ignore[empty-body]


# start_custom_condition
import dagster as dg


class IsCompanyHoliday(dg.AutomationCondition):
    def evaluate(self, context: dg.AutomationContext) -> dg.AutomationResult:
        if is_company_holiday(context.evaluation_time):
            true_subset = context.candidate_subset
        else:
            true_subset = context.get_empty_subset()
        return dg.AutomationResult(true_subset, context=context)  # ty: ignore[invalid-argument-type, missing-argument, parameter-already-assigned]


# end_custom_condition


# start_conditional
import dagster as dg

condition = dg.AutomationCondition.eager() & ~IsCompanyHoliday()


# end_conditional
