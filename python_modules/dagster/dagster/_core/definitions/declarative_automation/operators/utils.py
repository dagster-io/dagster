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
        SinceCondition,
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
        "SinceCondition",
    ]
]:
    from dagster._core.definitions.declarative_automation.operators import (
        AndAutomationCondition,
        ChecksAutomationCondition,
        DepsAutomationCondition,
        NotAutomationCondition,
        OrAutomationCondition,
        SinceCondition,
    )

    return isinstance(
        condition,
        (
            AndAutomationCondition,
            ChecksAutomationCondition,
            DepsAutomationCondition,
            NotAutomationCondition,
            OrAutomationCondition,
            SinceCondition,
        ),
    )
