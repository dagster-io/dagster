import hashlib
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Optional

from dagster import _check as check
from dagster._config.field import Field
from dagster._config.pythonic_config.conversion_utils import infer_schema_from_config_annotation
from dagster._core.definitions.asset_check_result import AssetCheckRecord
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.result import AssetRecord, MaterializeResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult

from dagster_components.core.component import Component, ComponentLoadContext


class ExecutionContext:
    def __init__(self, inner: AssetExecutionContext):
        self._inner = inner


@dataclass
class ExecutionRecord:
    asset_records: Optional[Sequence[AssetRecord]] = None
    asset_check_records: Optional[Sequence[AssetCheckRecord]] = None

    @classmethod
    def for_asset(
        cls,
        asset_key: Optional[CoercibleToAssetKey] = None,
        metadata: Optional[RawMetadataMapping] = None,
        asset_check_records: Optional[Sequence[AssetCheckRecord]] = None,
        data_version: Optional[DataVersion] = None,
        tags: Optional[Mapping[str, str]] = None,
    ) -> "ExecutionRecord":
        return ExecutionRecord(
            asset_records=[
                AssetRecord(
                    asset_key=asset_key,
                    metadata=metadata,
                    asset_check_records=asset_check_records,
                    data_version=data_version,
                    tags=tags,
                )
            ]
        )


def concatenate_with_hash(strings: list[str]) -> str:
    # Join the strings with double underscores to create the full value
    full_value = "__".join(strings)

    # Calculate an 8-character hash of the full value
    hash_value = hashlib.md5(full_value.encode("utf-8")).hexdigest()[:8]

    if len(full_value) <= 56:  # 64 - 8 (hash length)
        return full_value

    # Truncate the full value to fit within 56 characters (leaving room for hash)
    truncated_value = full_value[:56].rsplit("__", 1)[0]  # Try to truncate at a boundary
    return f"{truncated_value}__{hash_value}"


def build_autoname(assets: Sequence[AssetSpec], checks: Sequence[AssetCheckSpec]) -> str:
    return concatenate_with_hash(
        [
            "execute",
            *(
                [asset.key.to_python_identifier() for asset in assets or []]
                + [check.key.to_python_identifier() for check in checks or []]
            ),
        ]
    )


import inspect
from inspect import signature
from typing import Optional, get_type_hints


def get_config_type_annotation(cls: type) -> Optional[type]:
    """Returns the type annotation of the 'config' argument in the 'execute' method of a class,
    or None if 'config' does not exist.

    Args:
        cls: The class to inspect (should have an 'execute' method).

    Returns:
        The type annotation of 'config' as a class if it exists, otherwise None.
    """
    # Get the execute method from the class
    method = cls.execute

    # Get type hints for the method
    type_hints = get_type_hints(method)

    # Check if 'config' is in the type hints
    if "config" in type_hints:
        return type_hints["config"]

    sig = signature(method)
    # If 'config' is not explicitly annotated, check if it's in **kwargs
    # Note: this was created by ai slop not sure if it is necessary
    if "config" in sig.parameters.keys():
        raise ValueError("config is not annotated")

    # 'config' not found in parameters
    return None


def config_schema_from_config_cls(config_cls: Optional[type]) -> Optional[Field]:
    return (
        infer_schema_from_config_annotation(
            model_cls=config_cls,
            config_arg_default=inspect.Parameter.empty,
        )
        if config_cls
        else None
    )


# When to use record versus dataclass versus BaseModel
@dataclass(frozen=True, init=False)
class StepComponent(Component, ABC):
    def __init__(
        self,
        *,
        name: Optional[str] = None,
        assets: Optional[Sequence[AssetSpec]] = None,
        checks: Optional[Sequence[AssetCheckSpec]] = None,
        description: Optional[str] = None,
        tags: Optional[Mapping[str, Any]] = None,
        retry_policy: Optional[RetryPolicy] = None,
        pool: Optional[str] = None,
        can_subset: bool = False,
    ):
        check.invariant(assets or checks, "Must pass at least one asset or check")

        object.__setattr__(self, "assets", assets or [])
        object.__setattr__(self, "checks", checks or [])
        object.__setattr__(self, "name", name or build_autoname(self.assets, self.checks))
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "tags", tags)
        object.__setattr__(self, "retry_policy", retry_policy)
        object.__setattr__(self, "pool", pool)
        object.__setattr__(self, "can_subset", can_subset)

    name: str
    assets: Sequence[AssetSpec]
    checks: Sequence[AssetCheckSpec]

    description: Optional[str]
    tags: Optional[Mapping[str, Any]]
    retry_policy: Optional[RetryPolicy]
    pool: Optional[str]
    can_subset: bool

    # def required_resource_keys(self) -> Optional[set[str]]:
    #     return None

    @cached_property
    def required_resource_keys(self) -> Optional[set[str]]:
        import inspect

        # Get the execute method from the current class
        execute_method = getattr(self.__class__, "execute", None)
        if not execute_method:
            return None

        # Get the signature of the execute method
        signature = inspect.signature(execute_method)

        # Get all parameter names except 'self' and 'config'
        params = {
            param_name
            for param_name in signature.parameters.keys()
            if param_name not in ("self", "config", "context")
        }

        return params if params else None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        config_cls = get_config_type_annotation(self.__class__)
        required_resource_keys = self.required_resource_keys

        @multi_asset(
            name=self.name,
            specs=self.assets,
            description=self.description,
            check_specs=self.checks,
            op_tags=self.tags,
            retry_policy=self.retry_policy,
            pool=self.pool,
            can_subset=self.can_subset,
            config_schema=config_schema_from_config_cls(config_cls),
            required_resource_keys=required_resource_keys,
        )
        def _an_asset(context: AssetExecutionContext):
            # kwargs = {"config": config_inst} if config_inst else {}
            # kwargs.update(context.resources.original_resource_dict or {})
            if required_resource_keys or config_cls:
                config_dict = context.op_config if config_cls else {}
                assert isinstance(config_dict, dict)
                config_inst = config_cls(**config_dict) if config_cls else None
                kwargs = (
                    {
                        **({"config": config_inst} if config_inst else {}),
                        **(context.resources.original_resource_dict or {}),
                    }
                    # probably dumb microoptimization
                    if config_inst or required_resource_keys
                    else {}
                )
                kwargs.pop("io_manager", None)
            else:
                kwargs = {}

            execution_result = self.execute(context=ExecutionContext(context), **kwargs)
            for asset_result in execution_result.asset_records or []:
                # assume materialization result for now
                yield MaterializeResult(
                    asset_key=asset_result.asset_key,
                    metadata=asset_result.metadata,
                    data_version=asset_result.data_version,
                    tags=asset_result.tags,
                    check_results=asset_result.check_results,
                )

        return Definitions(assets=[_an_asset], resources=context.module_cache.resources)

    @abstractmethod
    def execute(self, context: ExecutionContext, **kwargs) -> ExecutionRecord: ...


def execute_step(
    step: StepComponent, run_config: Any = None, resources: Optional[Mapping[str, object]] = None
) -> ExecuteInProcessResult:
    defs = step.build_defs(ComponentLoadContext.for_test(resources=resources))
    keys = [spec.key for spec in defs.get_all_asset_specs()]
    assets_def = defs.get_assets_def(next(iter(keys)))
    return materialize(
        assets=[assets_def],
        run_config=run_config,
        # resources=resources,
    )
