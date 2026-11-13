from typing import TYPE_CHECKING, Union

from typing_extensions import TypeIs

from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)

if TYPE_CHECKING:
    from dagster._core.definitions.declarative_automation.operators import (
        AndAutomationCondition,
        BaseDepsAutomationCondition,
        ChecksAutomationCondition,
        NotAutomationCondition,
        OrAutomationCondition,
        SinceCondition,
    )


def has_allow_ignore(
    condition: AutomationCondition,
) -> TypeIs[
    Union[
        "AndAutomationCondition",
        "BaseDepsAutomationCondition",
        "ChecksAutomationCondition",
        "NotAutomationCondition",
        "OrAutomationCondition",
        "SinceCondition",
    ]
]:
    from dagster._core.definitions.declarative_automation.operators import (
        AndAutomationCondition,
        BaseDepsAutomationCondition,
        ChecksAutomationCondition,
        NotAutomationCondition,
        OrAutomationCondition,
        SinceCondition,
    )

    return isinstance(
        condition,
        (
            AndAutomationCondition,
            BaseDepsAutomationCondition,
            ChecksAutomationCondition,
            NotAutomationCondition,
            OrAutomationCondition,
            SinceCondition,
        ),
    )


def has_resolve_through_virtual(
    condition: AutomationCondition,
) -> TypeIs[
    Union[
        "AndAutomationCondition",
        "BaseDepsAutomationCondition",
        "NotAutomationCondition",
        "OrAutomationCondition",
        "SinceCondition",
    ]
]:
    from dagster._core.definitions.declarative_automation.operators import (
        AndAutomationCondition,
        BaseDepsAutomationCondition,
        NotAutomationCondition,
        OrAutomationCondition,
        SinceCondition,
    )

    return isinstance(
        condition,
        (
            AndAutomationCondition,
            BaseDepsAutomationCondition,
            NotAutomationCondition,
            OrAutomationCondition,
            SinceCondition,
        ),
    )
