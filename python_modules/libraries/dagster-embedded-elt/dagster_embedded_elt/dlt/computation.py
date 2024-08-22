import hashlib
from functools import cached_property
from typing import Callable, Iterable, List, Optional, Sequence, Union

from dagster import (
    AssetSpec,
    _check as check,
)
from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.result import MaterializeResult, ObserveResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from typing_extensions import TypeAlias


class Specs:
    def __init__(self, specs: Sequence[Union[AssetSpec, AssetCheckSpec]]):
        self.specs = list(
            check.opt_sequence_param(specs, "specs", of_type=(AssetSpec, AssetCheckSpec)) or []
        )

    def replace(self, **kwargs) -> "Specs":
        self.specs = [spec._replace(**kwargs) for spec in self.specs]
        return self

    def with_tags(self, tags: dict) -> "Specs":
        self.specs = [
            spec._replace(tags={**spec.tags, **tags}) if isinstance(spec, AssetSpec) else spec
            for spec in self.specs
        ]
        return self

    def with_metadata(self, metadata: dict) -> "Specs":
        self.specs = [
            spec._replace(metadata={**(spec.metadata or {}), **metadata}) for spec in self.specs
        ]
        return self

    def apply(
        self, f: Callable[[Union[AssetSpec, AssetCheckSpec]], Union[AssetSpec, AssetCheckSpec]]
    ) -> "Specs":
        self.specs = [f(spec) for spec in self.specs]
        return self

    def to_list(self) -> List[Union[AssetSpec, AssetCheckSpec]]:
        return self.specs

    def to_asset_specs(self) -> List[AssetSpec]:
        return [spec for spec in self.specs if isinstance(spec, AssetSpec)]


class ComputationContext:
    def __init__(self, context: AssetExecutionContext):
        self._ae_context = context

    # this property here to not freak people out temporarily
    @property
    def partition_key(self) -> Optional[str]:
        return self._ae_context.partition_key

    def to_asset_execution_context(self) -> AssetExecutionContext:
        return self._ae_context


def iterate_comps(specs: Sequence[Union[AssetSpec, AssetCheckSpec]]) -> Iterable[str]:
    return [
        spec.get_python_identifier()
        if isinstance(spec, AssetCheckSpec)
        else spec.key.to_python_identifier()
        for spec in specs
    ]


def unique_name(specs: Sequence[Union[AssetSpec, AssetCheckSpec]]) -> str:
    return hashlib.sha256("_".join(sorted(set(iterate_comps(specs)))).encode()).hexdigest()[:32]


SpecsArg: TypeAlias = Union[Specs, Sequence[Union[AssetSpec, AssetCheckSpec]]]
SpecResult: TypeAlias = Union[MaterializeResult, AssetCheckResult, ObserveResult]


class ComputationResult:
    def __init__(self, spec_results: Sequence[SpecResult], execution_metadata=None) -> None:
        self.spec_results = list(
            check.opt_sequence_param(spec_results, "spec_results", of_type=SpecResult) or []
        )
        self.execution_metadata = execution_metadata or {}


class ExecutionComplete:
    def __init__(self, execution_metadata=None) -> None:
        self.execution_metadata = execution_metadata or {}


class Computation:
    def __init__(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        specs: SpecsArg,
        tags: Optional[dict] = None,
        config_schema: Optional[UserConfigSchema] = None,
    ):
        self.specs: List[Union[AssetSpec, AssetCheckSpec]] = (
            specs.to_list()
            if isinstance(specs, Specs)
            else list(check.sequence_param(specs, "specs", of_type=(AssetSpec, AssetCheckSpec)))
        )
        self.name = name or unique_name(self.specs)
        self.tags = tags
        self.config_schema = config_schema
        self.description = description

    @property
    def asset_specs(self) -> List[AssetSpec]:
        return [spec for spec in self.specs if isinstance(spec, AssetSpec)]

    @property
    def asset_check_specs(self) -> List[AssetCheckSpec]:
        return [spec for spec in self.specs if isinstance(spec, AssetCheckSpec)]

    def execute(self, context: ComputationContext, **kwargs) -> ComputationResult:
        results_or_complete = list(self.stream(context, **kwargs))

        complete = next(
            (result for result in results_or_complete if isinstance(result, ExecutionComplete)),
            None,
        )
        return ComputationResult(
            spec_results=[
                result for result in results_or_complete if isinstance(result, SpecResult)
            ],
            execution_metadata=complete.execution_metadata if complete else None,
        )

    def stream(
        self, context: ComputationContext, **kwargs
    ) -> Iterable[Union[SpecResult, ExecutionComplete]]: ...

    def test(self, partitions: Optional[str] = None) -> ExecuteInProcessResult:
        # TODO handle all partition varietals (list, range)
        return materialize([self.assets_def], partition_key=partitions)

    @cached_property
    def assets_def(self) -> AssetsDefinition:
        @multi_asset(
            name=self.name,
            specs=self.asset_specs,
            check_specs=self.asset_check_specs,
            op_tags=self.tags,
            config_schema=self.config_schema,
            description=self.description,
        )
        def inst(context: AssetExecutionContext):
            for r in self.stream(ComputationContext(context)):
                if isinstance(r, SpecResult):
                    yield r

        return inst
