import inspect
from abc import ABC, abstractmethod
from functools import cached_property
from typing import (
    Iterable,
    Optional,
    Sequence,
    Set,
    Union,
)

from dagster import _check as check
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
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
)
from dagster._utils.security import non_secure_md5_hash_str


def resources_without_io_manager(context: AssetExecutionContext):
    original_resources = context.resources.original_resource_dict
    return {k: v for k, v in original_resources.items() if k != "io_manager"}


def unique_id_from_key(keys: Sequence[AssetKeyOrCheckKey]) -> str:
    """Generate a unique ID from the provided keys.

    This is necessary to disambiguate between different ops underlying sections without
    forcing the user to provide a name for the underlying op.
    """
    sorted_keys = sorted(keys, key=lambda key: key.to_string())
    return non_secure_md5_hash_str(",".join([str(key) for key in sorted_keys]).encode())[:8]


EntitySetExecuteResult = Iterable[Union[MaterializeResult, AssetCheckResult, ObserveResult]]


class ExecutableEntitySet(ABC):
    def __init__(
        self,
        specs: Sequence[Union[AssetSpec, AssetCheckSpec]],
        compute_kind: Optional[str] = None,
        subsettable: bool = False,
        tags: Optional[dict] = None,
        friendly_name: Optional[str] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        # TODO implement these
        # backfill_policy: Optional[BackfillPolicy] = None,
        # retry_policy: Optional[RetryPolicy] = None,
        # config_schema: Optional[UserConfigSchema] = None,
    ):
        self.specs = specs
        self._compute_kind = compute_kind
        self._subsettable = subsettable
        self._tags = tags or {}
        self._friendly_name = friendly_name or unique_id_from_key([spec.key for spec in self.specs])
        self._partitions_def = partitions_def

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

    @property
    def asset_specs(self) -> Sequence[AssetSpec]:
        return [spec for spec in self.specs if isinstance(spec, AssetSpec)]

    @property
    def asset_check_specs(self) -> Sequence[AssetCheckSpec]:
        return [spec for spec in self.specs if isinstance(spec, AssetCheckSpec)]

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
                    context=context,
                    **self._only_required_resources(context.resources.original_resource_dict),
                )

            return _nope_multi_asset
        else:
            return self.to_asset_checks_def()

    def to_asset_checks_def(self) -> AssetChecksDefinition:
        check.invariant(
            not self._partitions_def,
            "PartitionsDefinition not supported for check-only ExecutableAssetGraphEntitySet",
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
                context=context,
                **self._only_required_resources(context.resources.original_resource_dict),
            )

        return _nope_multi_asset_check

    # Resources as kwargs. Must match set in required_resource_keys.
    # If the user has only specified asset checks, they can override typed as AssetCheckExecutionContext
    # instead. It would be preferable to have a unified context.
    @abstractmethod
    def execute(
        self, context: Union[AssetCheckExecutionContext, AssetExecutionContext], **kwargs
    ) -> EntitySetExecuteResult: ...
