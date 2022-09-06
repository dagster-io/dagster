from typing import TYPE_CHECKING, Callable

import dagster._check as check

if TYPE_CHECKING:
    from dagster._core.execution.context.asset_expectation import AssetExpectationContext


class AssetExpectationDefinition:
    def __init__(
        self,
        name: str,
        expectation_fn: Callable[["AssetExpectationContext"], bool],
    ):
        self._name = check.str_param(name, "name")
        self._expectation_fn = check.callable_param(expectation_fn, "expectation_fn")

    @property
    def expectation_fn(self) -> Callable[["AssetExpectationContext"], bool]:
        return self._expectation_fn

    @property
    def name(self) -> str:
        return self._name
