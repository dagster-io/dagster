from typing import TYPE_CHECKING, Callable, Optional, overload

import dagster._check as check

from ..asset_expectation import AssetExpectationDefinition

if TYPE_CHECKING:
    from dagster._core.execution.context.asset_expectation import AssetExpectationContext


class _AssetExpectation:
    def __init__(self, name: Optional[str] = None):
        self._name = name

    def __call__(
        self, fn: Callable[["AssetExpectationContext"], bool]
    ) -> AssetExpectationDefinition:
        check.callable_param(fn, "fn")
        return AssetExpectationDefinition(expectation_fn=fn, name=self._name or fn.__name__)


@overload
def asset_expectation(
    expectation_fn: Callable[["AssetExpectationContext"], bool],
) -> AssetExpectationDefinition:
    ...


@overload
def asset_expectation(*, name: Optional[str] = None) -> _AssetExpectation:
    ...


def asset_expectation(
    expectation_fn: Callable[["AssetExpectationContext"], bool], *, name: Optional[str] = None
) -> _AssetExpectation:
    if expectation_fn is not None:
        return _AssetExpectation()(expectation_fn)

    return _AssetExpectation(name=name)
