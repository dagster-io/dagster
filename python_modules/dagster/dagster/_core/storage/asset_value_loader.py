from collections.abc import Mapping
from contextlib import ExitStack
from typing import Any, Optional, cast

import dagster._check as check
from dagster._annotations import deprecated_param, public
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.job_definition import (
    default_job_io_manager_with_fs_io_manager_schema,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.utils import DEFAULT_IO_MANAGER_KEY
from dagster._core.execution.build_resources import build_resources, get_mapped_resource_config
from dagster._core.execution.context.input import build_input_context
from dagster._core.execution.context.output import build_output_context
from dagster._core.execution.resources_init import get_transitive_required_resource_keys
from dagster._core.instance import DagsterInstance
from dagster._core.instance.config import is_dagster_home_set
from dagster._core.storage.io_manager import IOManager
from dagster._core.types.dagster_type import resolve_dagster_type
from dagster._utils.merger import merge_dicts
from dagster._utils.warnings import normalize_renamed_param


class AssetValueLoader:
    """Caches resource definitions that are used to load asset values across multiple load
    invocations.

    Should not be instantiated directly. Instead, use
    :py:meth:`~dagster.RepositoryDefinition.get_asset_value_loader`.
    """

    def __init__(
        self,
        assets_defs_by_key: Mapping[AssetKey, AssetsDefinition],
        instance: Optional[DagsterInstance] = None,
    ):
        self._assets_defs_by_key = assets_defs_by_key
        self._resource_instance_cache: dict[str, object] = {}
        self._exit_stack: ExitStack = ExitStack().__enter__()
        if not instance and is_dagster_home_set():
            self._instance = self._exit_stack.enter_context(DagsterInstance.get())
        else:
            self._instance = instance

    def _ensure_resource_instances_in_cache(
        self,
        resource_defs: Mapping[str, ResourceDefinition],
        resource_config: Optional[Mapping[str, Any]] = None,
    ):
        for built_resource_key, built_resource in (
            self._exit_stack.enter_context(
                build_resources(
                    resources={
                        resource_key: self._resource_instance_cache.get(resource_key, resource_def)
                        for resource_key, resource_def in resource_defs.items()
                    },
                    instance=self._instance,
                    resource_config=resource_config,
                )
            )
            ._asdict()
            .items()
        ):
            self._resource_instance_cache[built_resource_key] = built_resource

    @deprecated_param(
        param="metadata",
        breaking_version="2.0",
        additional_warn_text="Use `input_definition_metadata` instead.",
    )
    @public
    def load_asset_value(
        self,
        asset_key: CoercibleToAssetKey,
        *,
        python_type: Optional[type[object]] = None,
        partition_key: Optional[str] = None,
        input_definition_metadata: Optional[dict[str, Any]] = None,
        resource_config: Optional[Mapping[str, Any]] = None,
        # deprecated
        metadata: Optional[dict[str, Any]] = None,
    ) -> object:
        """Loads the contents of an asset as a Python object.

        Invokes `load_input` on the :py:class:`IOManager` associated with the asset.

        Args:
            asset_key (Union[AssetKey, Sequence[str], str]): The key of the asset to load.
            python_type (Optional[Type]): The python type to load the asset as. This is what will
                be returned inside `load_input` by `context.dagster_type.typing_type`.
            partition_key (Optional[str]): The partition of the asset to load.
            input_definition_metadata (Optional[Dict[str, Any]]): Input metadata to pass to the :py:class:`IOManager`
                (is equivalent to setting the metadata argument in `In` or `AssetIn`).
            resource_config (Optional[Any]): A dictionary of resource configurations to be passed
                to the :py:class:`IOManager`.

        Returns:
            The contents of an asset as a Python object.
        """
        asset_key = AssetKey.from_coercible(asset_key)
        resource_config = resource_config or {}
        output_definition_metadata = {}

        if asset_key in self._assets_defs_by_key:
            assets_def = self._assets_defs_by_key[asset_key]

            resource_defs = merge_dicts(
                {DEFAULT_IO_MANAGER_KEY: default_job_io_manager_with_fs_io_manager_schema},
                assets_def.resource_defs,
            )
            io_manager_key = assets_def.get_io_manager_key_for_asset_key(asset_key)
            io_manager_def = resource_defs[io_manager_key]
            name = (
                assets_def.get_output_name_for_asset_key(asset_key)
                if assets_def.is_executable
                else None
            )
            output_definition_metadata = assets_def.specs_by_key[asset_key].metadata
            op_def = assets_def.get_op_def_for_asset_key(asset_key)
            asset_partitions_def = assets_def.partitions_def
        else:
            check.failed(f"Asset key {asset_key} not found")

        required_resource_keys = get_transitive_required_resource_keys(
            io_manager_def.required_resource_keys, resource_defs
        ) | {io_manager_key}

        self._ensure_resource_instances_in_cache(
            {k: v for k, v in resource_defs.items() if k in required_resource_keys},
            resource_config=resource_config,
        )
        io_manager = cast(IOManager, self._resource_instance_cache[io_manager_key])

        io_config = resource_config.get(io_manager_key)
        io_resource_config = {io_manager_key: io_config} if io_config else {}

        io_manager_config = get_mapped_resource_config(
            {io_manager_key: io_manager_def}, io_resource_config
        )

        input_context = build_input_context(
            name=None,
            asset_key=asset_key,
            dagster_type=resolve_dagster_type(python_type),
            upstream_output=build_output_context(
                name=name,
                definition_metadata=output_definition_metadata,
                asset_key=asset_key,
                op_def=op_def,
                resource_config=resource_config,
            ),
            resources=self._resource_instance_cache,
            resource_config=io_manager_config[io_manager_key].config,
            partition_key=partition_key,
            asset_partition_key_range=(
                PartitionKeyRange(partition_key, partition_key)
                if partition_key is not None
                else None
            ),
            asset_partitions_def=asset_partitions_def,
            instance=self._instance,
            definition_metadata=normalize_renamed_param(
                input_definition_metadata, "input_definition_metadata", metadata, "metadata"
            ),
        )

        return io_manager.load_input(input_context)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._exit_stack.close()
