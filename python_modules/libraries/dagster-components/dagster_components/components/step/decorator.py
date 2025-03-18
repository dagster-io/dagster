from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional

from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.policy import RetryPolicy
from typing_extensions import TypeAlias

from dagster_components.components.step.step import ExecutionContext, ExecutionRecord, StepComponent
from dagster_components.core.component import ComponentLoadContext, component

ExecutionFn: TypeAlias = Callable[[ExecutionContext], ExecutionRecord]


# TODO: need to get typehinting to work better with less gross __init__ method
# TODO: support config and resources
@dataclass(frozen=True, init=False)
class DecoratedBasedStepComponent(StepComponent):
    def __init__(self, fn: ExecutionFn, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, "fn", fn)

    fn: ExecutionFn

    def execute(self, context, **kwargs):
        return self.fn(context, **kwargs)


ComponentLoader = Callable[[ComponentLoadContext], DecoratedBasedStepComponent]


def step(
    *,
    name: Optional[str] = None,
    assets: Optional[Sequence[AssetSpec]] = None,
    checks: Optional[Sequence[AssetCheckSpec]] = None,
    description: Optional[str] = None,
    tags: Optional[Mapping[str, Any]] = None,
    retry_policy: Optional[RetryPolicy] = None,
    pool: Optional[str] = None,
    can_subset: bool = False,
) -> Callable[[ExecutionFn], ComponentLoader]:
    def inner(fn: ExecutionFn) -> ComponentLoader:
        @component
        def load_me(context: ComponentLoadContext) -> DecoratedBasedStepComponent:
            return DecoratedBasedStepComponent(
                name=name,
                assets=assets,
                checks=checks,
                description=description,
                tags=tags,
                retry_policy=retry_policy,
                pool=pool,
                can_subset=can_subset,
                fn=fn,
            )

        return load_me

    return inner
