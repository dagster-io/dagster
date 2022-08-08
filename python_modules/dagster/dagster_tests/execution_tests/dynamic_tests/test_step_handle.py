from dagster._core.execution.plan.handle import (
    ResolvedFromDynamicStepHandle,
    StepHandle,
    UnresolvedStepHandle,
)
from dagster import Out, op


def test_step_handles():
    plain = StepHandle.parse_from_key("foo")
    assert isinstance(plain, StepHandle)
    unresolved = StepHandle.parse_from_key("foo[?]")
    assert isinstance(unresolved, UnresolvedStepHandle)
    resolved = StepHandle.parse_from_key("foo[bar]")
    assert isinstance(resolved, ResolvedFromDynamicStepHandle)

    assert unresolved.resolve("bar") == resolved

    assert resolved.unresolved_form == unresolved
