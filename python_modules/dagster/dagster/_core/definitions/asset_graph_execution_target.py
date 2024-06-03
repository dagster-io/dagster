import inspect
from abc import ABC, abstractmethod
from functools import cached_property
from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Union,
)

from dagster import _check as check
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.base_asset_graph import AssetKeyOrCheckKey
from dagster._core.definitions.decorators.asset_check_decorator import multi_asset_check
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.result import MaterializeResult, ObserveResult
from dagster._core.execution.context.compute import (
    AssetCheckExecutionContext,
    AssetExecutionContext,
    OpExecutionContext,
)
from dagster._utils.security import non_secure_md5_hash_str


def unique_id_from_key(keys: Sequence[AssetKeyOrCheckKey]) -> str:
    """Generate a unique ID from the provided keys.

    This is necessary to disambiguate between different ops underlying sections without
    forcing the user to provide a name for the underlying op.
    """
    sorted_keys = sorted(keys, key=lambda key: key.to_string())
    return non_secure_md5_hash_str(",".join([str(key) for key in sorted_keys]).encode())[:8]


AssetGraphExecutionResult = Iterable[Union[MaterializeResult, AssetCheckResult, ObserveResult]]


# This is a placeholder for now. I think this is an opportunity to unify all of
# our contexts with final, canonical object that works for any execution
# happening in the context of the asset graph.
class AssetGraphExecutionContext:
    __slots__ = ["_context"]

    def __init__(self, context: Union[AssetExecutionContext, AssetCheckExecutionContext]):
        self._context = context

    def to_op_execution_context(self) -> OpExecutionContext:
        return self._context.op_execution_context


class AssetDefinition(NamedTuple):
    key: AssetKey
    group_name: Optional[str]
    description: Optional[str]
    deps: Optional[Iterable[AssetDep]]
    tags: Optional[Mapping[str, str]]
    metadata: Optional[Mapping[str, Any]]
    partitions_def: Optional[PartitionsDefinition]

    @property
    def compute_kind(self) -> Optional[str]:
        return (self.tags or {}).get("dagster/compute_kind")

    def reconstruct_asset_spec(self) -> AssetSpec:
        return AssetSpec(
            key=self.key,
            group_name=self.group_name,
            description=self.description,
            deps=self.deps,
            tags=self.tags,
            metadata=self.metadata,
        )

    @staticmethod
    def partitioned(
        asset_specs: Sequence[AssetSpec], partitions_def: Optional[PartitionsDefinition]
    ) -> List["AssetDefinition"]:
        return [
            AssetDefinition(
                key=spec.key,
                group_name=spec.group_name,
                description=spec.description,
                deps=spec.deps,
                tags=spec.tags,
                metadata=spec.metadata,
                partitions_def=partitions_def,
            )
            for spec in asset_specs
        ]

    def with_compute_kind(self, compute_kind: str) -> "AssetDefinition":
        return self._replace(tags={**(self.tags or {}), "dagster/compute_kind": compute_kind})


class AssetCheckDefinition(NamedTuple):
    name: str
    asset_key: AssetKey
    description: Optional[str]
    partitions_def: Optional[PartitionsDefinition]

    @staticmethod
    def partioned(
        check_specs: Sequence[AssetCheckSpec], partitions_def: Optional[PartitionsDefinition]
    ) -> List["AssetCheckDefinition"]:
        return [
            AssetCheckDefinition(
                name=spec.name,
                asset_key=spec.asset_key,
                description=spec.description,
                partitions_def=partitions_def,
            )
            for spec in check_specs
        ]

    def reconstruct_asset_check_spec(self) -> AssetCheckSpec:
        return AssetCheckSpec(
            name=self.name,
            asset=self.asset_key,
            description=self.description,
        )


class AssetGraphExecutionTarget(ABC):
    def __init__(
        self,
        defs: Sequence[Union[AssetDefinition, AssetCheckDefinition]],
        friendly_name: Optional[str] = None,
        subsettable: bool = False,
        tags: Optional[dict] = None,
        compute_kind: Optional[str] = None,
        # TODO implement these
        # backfill_policy: Optional[BackfillPolicy] = None,
        # retry_policy: Optional[RetryPolicy] = None,
        # config_schema: Optional[UserConfigSchema] = None,
    ):
        self.defs = defs
        self._tags = tags or {}
        self._friendly_name = friendly_name or unique_id_from_key(
            [spec.key for spec in self.asset_defs]
        )
        self._partitions_def = None  # TODO
        self._subsettable = subsettable
        self._compute_kind = (
            compute_kind if compute_kind else self._infer_compute_def(self.asset_defs)
        )

    def _infer_compute_def(self, asset_defs: Iterable[AssetDefinition]) -> Optional[str]:
        compute_kinds = {def_.compute_kind for def_ in asset_defs if def_.compute_kind is not None}
        return compute_kinds.pop() if len(compute_kinds) == 1 else None

    @cached_property
    def asset_defs(self) -> List[AssetDefinition]:
        return [def_ for def_ in self.defs if isinstance(def_, AssetDefinition)]

    @cached_property
    def asset_check_defs(self) -> List[AssetCheckDefinition]:
        return [def_ for def_ in self.defs if isinstance(def_, AssetCheckDefinition)]

    @property
    def required_resource_keys(self) -> Set[str]:
        # calling inner property to cache property while
        # still allowing a user to override this
        return self._cached_required_resource_keys

    @cached_property
    def _cached_required_resource_keys(self) -> Set[str]:
        execute_method = getattr(self, "execute")
        parameters = inspect.signature(execute_method).parameters
        return {param for param in parameters if param != "context"}

    @cached_property
    def asset_specs(self) -> Sequence[AssetSpec]:
        return [asset_def.reconstruct_asset_spec() for asset_def in self.asset_defs]

    @cached_property
    def asset_check_specs(self) -> Sequence[AssetCheckSpec]:
        return [check_def.reconstruct_asset_check_spec() for check_def in self.asset_check_defs]

    @property
    def op_name(self) -> str:
        return self._friendly_name

    @property
    def tags(self) -> Optional[dict]:
        return self._tags

    @property
    def subsettable(self) -> bool:
        return self._subsettable

    @property
    def compute_kind(self) -> Optional[str]:
        return self._compute_kind

    def _only_required_resources(self, original_resource_dict: dict):
        return {k: v for k, v in original_resource_dict.items() if k in self.required_resource_keys}

    def to_assets_def(self) -> AssetsDefinition:
        if self.asset_specs:

            @multi_asset(
                specs=self.asset_specs,
                check_specs=self.asset_check_specs,
                name=self.op_name,
                op_tags=self.tags,
                required_resource_keys=self.required_resource_keys,
                compute_kind=self.compute_kind,
                can_subset=self.subsettable,
                partitions_def=self._partitions_def,
            )
            def _nope_multi_asset(context: AssetExecutionContext):
                return self.execute(
                    context=AssetGraphExecutionContext(context),
                    **self._only_required_resources(context.resources.original_resource_dict),
                )

            return _nope_multi_asset
        else:
            return self.to_asset_checks_def()

    def to_asset_checks_def(self) -> AssetChecksDefinition:
        check.invariant(
            not self._partitions_def,
            f"PartitionsDefinition not supported for check-only {type(self)}",
        )

        @multi_asset_check(
            specs=self.asset_check_specs,
            name=self.op_name,
            op_tags=self.tags,
            required_resource_keys=self.required_resource_keys,
            compute_kind=self.compute_kind,
            can_subset=self.subsettable,
        )
        def _nope_multi_asset_check(context: AssetCheckExecutionContext):
            return self.execute(
                context=AssetGraphExecutionContext(context),
                **self._only_required_resources(context.resources.original_resource_dict),
            )

        return _nope_multi_asset_check

    # Resources as kwargs. Must match set in required_resource_keys.
    # If the user has only specified asset checks, they can override typed as AssetCheckExecutionContext
    # instead. It would be preferable to have a unified context.
    @abstractmethod
    def execute(
        self, context: AssetGraphExecutionContext, **kwargs
    ) -> AssetGraphExecutionResult: ...
