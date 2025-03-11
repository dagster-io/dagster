from typing import TYPE_CHECKING, Union

from typing_extensions import TypeIs

from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)

if TYPE_CHECKING:
    from dagster._core.definitions.declarative_automation.operators import (
        AndAutomationCondition,
        ChecksAutomationCondition,
        DepsAutomationCondition,
        NotAutomationCondition,
        OrAutomationCondition,
    )


def has_allow_ignore(
    condition: AutomationCondition,
) -> TypeIs[
    Union[
        "AndAutomationCondition",
        "ChecksAutomationCondition",
        "DepsAutomationCondition",
        "NotAutomationCondition",
        "OrAutomationCondition",
    ]
]:
    from dagster._core.definitions.declarative_automation.operators import (
        AndAutomationCondition,
        ChecksAutomationCondition,
        DepsAutomationCondition,
        NotAutomationCondition,
        OrAutomationCondition,
    )

    return isinstance(
        condition,
        (
            AndAutomationCondition,
            ChecksAutomationCondition,
            DepsAutomationCondition,
            NotAutomationCondition,
            OrAutomationCondition,
        ),
    )
