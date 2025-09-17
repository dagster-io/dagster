from dagster._core.definitions.declarative_automation.operands.operands import (
    BackfillInProgressAutomationCondition as BackfillInProgressAutomationCondition,
    CheckResultCondition as CheckResultCondition,
    CodeVersionChangedCondition as CodeVersionChangedCondition,
    CronTickPassedCondition as CronTickPassedCondition,
    ExecutionFailedAutomationCondition as ExecutionFailedAutomationCondition,
    InitialEvaluationCondition as InitialEvaluationCondition,
    InLatestTimeWindowCondition as InLatestTimeWindowCondition,
    MissingAutomationCondition as MissingAutomationCondition,
    NewlyRequestedCondition as NewlyRequestedCondition,
    NewlyUpdatedCondition as NewlyUpdatedCondition,
    RunInProgressAutomationCondition as RunInProgressAutomationCondition,
    WillBeRequestedCondition as WillBeRequestedCondition,
)
from dagster._core.definitions.declarative_automation.operands.run_operands import (
    AllNewUpdatesHaveRunTagsCondition as AllNewUpdatesHaveRunTagsCondition,
    AnyNewUpdateHasRunTagsCondition as AnyNewUpdateHasRunTagsCondition,
    LatestRunExecutedWithRootTargetCondition as LatestRunExecutedWithRootTargetCondition,
    LatestRunExecutedWithTagsCondition as LatestRunExecutedWithTagsCondition,
)
