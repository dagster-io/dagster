from functools import wraps
from typing import (
    Any,
    Callable,
    Generator,
    Iterator,
    Mapping,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)
from dagster import (
    op,
    AssetsDefinition,
    OpExecutionContext,
    ConfigurableResource,
    AssetObservation,
    Output,
    Out,
    In,
    Nothing,
    asset,
    materialize_to_memory,
)
from typing_extensions import ParamSpec
import dagster._check as check
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.decorators.op_decorator import is_context_provided
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.input import In
from dagster._core.definitions.metadata import MetadataUserInput
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.execution.context.invocation import build_op_context
from dagster_dbt.utils import select_unique_ids_from_manifest, default_node_info_to_asset_key
from dagster_dbt.asset_defs import _get_deps, _get_node_description

from dbt.contracts.graph.manifest import WritableManifest


class DbtExecutionContext(OpExecutionContext):
    def __init__(
        self,
        op_context: OpExecutionContext,
        manifest: WritableManifest,
        base_select: str,
        base_exclude: Optional[str],
        key_by_unique_id: Mapping[str, AssetKey],
    ):
        super().__init__(op_context._step_execution_context)
        self._manifest = manifest
        self._base_select = base_select
        self._base_exclude = base_exclude
        self._key_by_unique_id = key_by_unique_id
        self._unique_id_by_key = {v: k for k, v in key_by_unique_id.items()}

    @property
    def all_selected(self) -> bool:
        return self.selected_output_names == len(self.op_def.output_defs)

    @property
    def dbt_select(self) -> str:
        explicit_select = " ".join(self.fqn_for_key(key) for key in self.selected_asset_keys)
        return self._base_select if self.all_selected else explicit_select

    @property
    def dbt_exclude(self) -> Optional[str]:
        return self._base_exclude if self.all_selected else None

    def key_for_unique_id(self, unique_id: str) -> AssetKey:
        return self._key_by_unique_id[unique_id]

    def unique_id_for_key(self, key: AssetKey) -> str:
        return self._unique_id_by_key[key]

    def node_info_for_key(self, key: AssetKey) -> Mapping[str, Any]:
        return self._manifest.nodes[self.unique_id_for_key(key)]

    def fqn_for_key(self, key: AssetKey) -> str:
        return ".".join(self.node_info_for_key(key)["fqn"])


def manifest_to_node_dict(manifest: WritableManifest) -> Mapping[str, Any]:
    raw_dict = manifest.to_dict()
    return {
        **raw_dict["nodes"],
        **raw_dict["sources"],
        **raw_dict["exposures"],
        **raw_dict["metrics"],
    }


def _chop(unique_id: str) -> str:
    return unique_id.split(".")[-1]


def dbt_assets(
    *,
    manifest_path: str,
    select: str = "*",
    exclude: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    asset_key_fn: Callable[[Mapping[str, Any]], AssetKey] = default_node_info_to_asset_key,
    freshness_policy_fn: Optional[Callable[[Mapping[str, Any]], Optional[FreshnessPolicy]]] = None,
    metadata_fn: Optional[Callable[[Mapping[str, Any]], Optional[MetadataUserInput]]] = None,
    op_name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
) -> Callable[..., AssetsDefinition]:
    manifest: WritableManifest = WritableManifest.read_and_check_versions(manifest_path)
    unique_ids = select_unique_ids_from_manifest(
        select=select, exclude=exclude or "", manifest_parsed=manifest
    )
    manifest_dict = manifest_to_node_dict(manifest)
    key_by_unique_id = {uid: asset_key_fn(manifest_dict[uid]) for uid in unique_ids}

    deps = _get_deps(
        manifest_dict,
        selected_unique_ids=unique_ids,
        asset_resource_types=["model", "seed", "snapshot"],
    )
    output_unique_ids = set(deps.keys())
    input_unique_ids = unique_ids - output_unique_ids

    def inner(fn) -> AssetsDefinition:
        @op(
            name=op_name,
            tags={"kind": "dbt"},
            ins={_chop(uid): In(Nothing) for uid in input_unique_ids},
            out={
                _chop(uid): Out(
                    dagster_type=Nothing,
                    description=_get_node_description(
                        manifest_dict[uid],
                        display_raw_sql=len(unique_ids) > 200,
                    ),
                    io_manager_key=io_manager_key,
                    is_required=False,
                )
                for uid in output_unique_ids
            },
        )
        @wraps(fn)
        def _op(*args, **kwargs):
            if is_context_provided(get_function_params(fn)):
                # convert the OpExecutionContext into a DbtExecutionContext, which has
                # additional context related to dbt
                return fn(
                    DbtExecutionContext(
                        cast(OpExecutionContext, args[0]),
                        manifest=manifest,
                        base_select=select,
                        base_exclude=exclude,
                        key_by_unique_id=key_by_unique_id,
                    ),
                    *args[1:],
                    **kwargs,
                )
            else:
                return fn(*args, **kwargs)

        return AssetsDefinition.from_op(
            _op,
            keys_by_input_name={_chop(uid): key_by_unique_id[uid] for uid in input_unique_ids},
            keys_by_output_name={_chop(uid): key_by_unique_id[uid] for uid in output_unique_ids},
            key_prefix=key_prefix,
            internal_asset_deps={
                _chop(uid): {key_by_unique_id[parent_uid] for parent_uid in parent_uids}
                for uid, parent_uids in deps.items()
            },
            partitions_def=partitions_def,
            metadata_by_output_name={
                _chop(uid): metadata_fn(manifest_dict[uid]) for uid in output_unique_ids
            }
            if metadata_fn
            else None,
            freshness_policies_by_output_name={
                _chop(uid): freshness_policy_fn(manifest_dict[uid]) for uid in output_unique_ids
            }
            if freshness_policy_fn
            else None,
        )

    return inner
