from dagster._core.definitions.declarative_automation.operands import (
    CodeVersionChangedCondition as CodeVersionChangedCondition,
    CronTickPassedCondition as CronTickPassedCondition,
    FailedAutomationCondition as FailedAutomationCondition,
    InLatestTimeWindowCondition as InLatestTimeWindowCondition,
    InProgressAutomationCondition as InProgressAutomationCondition,
    MissingAutomationCondition as MissingAutomationCondition,
    NewlyRequestedCondition as NewlyRequestedCondition,
    NewlyUpdatedCondition as NewlyUpdatedCondition,
    WillBeRequestedCondition as WillBeRequestedCondition,
)
from dagster._core.definitions.declarative_automation.operators import (
    AllDepsCondition as AllDepsCondition,
    AndAutomationCondition as AndAutomationCondition,
    AnyDepsCondition as AnyDepsCondition,
    AnyDownstreamConditionsCondition as AnyDownstreamConditionsCondition,
    NewlyTrueCondition as NewlyTrueCondition,
    NotAutomationCondition as NotAutomationCondition,
    OrAutomationCondition as OrAutomationCondition,
    SinceCondition as SinceCondition,
)
