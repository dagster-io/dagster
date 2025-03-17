from dagster._core.definitions.declarative_automation.operators.any_downstream_conditions_operator import (
    AnyDownstreamConditionsCondition as AnyDownstreamConditionsCondition,
)
from dagster._core.definitions.declarative_automation.operators.boolean_operators import (
    AndAutomationCondition as AndAutomationCondition,
    NotAutomationCondition as NotAutomationCondition,
    OrAutomationCondition as OrAutomationCondition,
)
from dagster._core.definitions.declarative_automation.operators.check_operators import (
    AllChecksCondition as AllChecksCondition,
    AnyChecksCondition as AnyChecksCondition,
    ChecksAutomationCondition as ChecksAutomationCondition,
)
from dagster._core.definitions.declarative_automation.operators.dep_operators import (
    AllDepsCondition as AllDepsCondition,
    AnyDepsCondition as AnyDepsCondition,
    DepsAutomationCondition as DepsAutomationCondition,
    EntityMatchesCondition as EntityMatchesCondition,
)
from dagster._core.definitions.declarative_automation.operators.newly_true_operator import (
    NewlyTrueCondition as NewlyTrueCondition,
)
from dagster._core.definitions.declarative_automation.operators.since_operator import (
    SinceCondition as SinceCondition,
)
