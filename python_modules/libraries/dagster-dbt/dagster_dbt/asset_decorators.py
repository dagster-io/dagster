from functools import wraps
from typing import Any, Callable, Mapping, Optional, Set, cast

from dagster import (
    AssetKey,
    AssetsDefinition,
    FreshnessPolicy,
    In,
    Nothing,
    OpExecutionContext,
    Out,
    PartitionsDefinition,
    op,
)
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.decorators.op_decorator import is_context_provided
from dagster._core.definitions.events import CoercibleToAssetKeyPrefix
from dagster._core.definitions.metadata import MetadataUserInput
from dbt.contracts.graph.manifest import WritableManifest

from dagster_dbt.asset_utils import (
    default_asset_key_fn,
    default_description_fn,
    default_freshness_policy_fn,
    default_group_fn,
    default_metadata_fn,
    get_deps,
)
from dagster_dbt.utils import select_unique_ids_from_manifest


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


class DbtExecutionContext(OpExecutionContext):
    """OpExecutionContext augmented with additional context related to dbt."""

    manifest: WritableManifest

    def __init__(
        self,
        op_context: OpExecutionContext,
        manifest: WritableManifest,
        base_select: str,
        base_exclude: Optional[str],
        key_by_unique_id: Mapping[str, AssetKey],
    ):
        super().__init__(op_context.get_step_execution_context())
        self.manifest = manifest
        self._manifest_dict = manifest_to_node_dict(manifest)
        self._base_select = base_select
        self._base_exclude = base_exclude
        self._key_by_unique_id = key_by_unique_id
        self._unique_id_by_key = {v: k for k, v in key_by_unique_id.items()}

    @property
    def all_selected(self) -> bool:
        return self.selected_output_names == len(self.op_def.output_defs)

    def get_dbt_selection_kwargs(self) -> Mapping[str, Any]:
        if self.all_selected:
            return {"select": self._base_select, "exclude": self._base_exclude}
        return {"select": " ".join(self.fqn_for_key(key) for key in self.selected_asset_keys)}

    def key_for_unique_id(self, unique_id: str) -> AssetKey:
        return self._key_by_unique_id[unique_id]

    def unique_id_for_key(self, key: AssetKey) -> str:
        return self._unique_id_by_key[key]

    def node_info_for_key(self, key: AssetKey) -> Mapping[str, Any]:
        return self._manifest_dict[self.unique_id_for_key(key)]

    def fqn_for_key(self, key: AssetKey) -> str:
        return ".".join(self.node_info_for_key(key)["fqn"])


def dbt_assets(
    *,
    manifest_path: str,
    select: str = "*",
    exclude: Optional[str] = None,
    models_only: bool = True,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    asset_key_fn: Callable[[Mapping[str, Any]], AssetKey] = default_asset_key_fn,
    freshness_policy_fn: Callable[
        [Mapping[str, Any]], Optional[FreshnessPolicy]
    ] = default_freshness_policy_fn,
    metadata_fn: Callable[[Mapping[str, Any]], Optional[MetadataUserInput]] = default_metadata_fn,
    group_fn: Callable[[Mapping[str, Any]], Optional[str]] = default_group_fn,
    op_name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    required_resource_keys: Optional[Set[str]] = None,
) -> Callable[..., AssetsDefinition]:
    manifest: WritableManifest = WritableManifest.read_and_check_versions(manifest_path)
    unique_ids = select_unique_ids_from_manifest(
        select=select, exclude=exclude or "", manifest_parsed=manifest
    )
    manifest_dict = manifest_to_node_dict(manifest)

    deps = get_deps(
        manifest_dict,
        selected_unique_ids=unique_ids,
        asset_resource_types=["model"] if models_only else ["model", "seed", "snapshot"],
    )
    output_unique_ids = set(deps.keys())
    input_unique_ids = set().union(*deps.values()) - output_unique_ids

    key_by_unique_id = {
        uid: asset_key_fn(manifest_dict[uid]) for uid in {*input_unique_ids, *output_unique_ids}
    }

    def inner(fn) -> AssetsDefinition:
        @op(
            name=op_name,
            tags={"kind": "dbt"},
            ins={_chop(uid): In(Nothing) for uid in input_unique_ids},
            out={
                _chop(uid): Out(
                    dagster_type=Nothing,
                    io_manager_key=io_manager_key,
                    is_required=False,
                )
                for uid in output_unique_ids
            },
            required_resource_keys=required_resource_keys,
        )
        @wraps(fn)
        def _op(*args, **kwargs):
            if is_context_provided(get_function_params(fn)):
                # convert the OpExecutionContext into a DbtExecutionContext, which has
                # additional context related to dbt
                yield from fn(
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
                yield from fn(*args, **kwargs)

        return AssetsDefinition.from_op(
            _op,
            keys_by_input_name={_chop(uid): key_by_unique_id[uid] for uid in input_unique_ids},
            keys_by_output_name={_chop(uid): key_by_unique_id[uid] for uid in output_unique_ids},
            key_prefix=key_prefix,
            partitions_def=partitions_def,
            internal_asset_deps={
                _chop(uid): {key_by_unique_id[parent_uid] for parent_uid in parent_uids}
                for uid, parent_uids in deps.items()
            },
            metadata_by_output_name={
                _chop(uid): metadata_fn(manifest_dict[uid]) for uid in output_unique_ids
            },
            freshness_policies_by_output_name={
                _chop(uid): freshness_policy_fn(manifest_dict[uid]) for uid in output_unique_ids
            },
            group_names_by_output_name={
                _chop(uid): group_fn(manifest_dict[uid]) for uid in output_unique_ids
            },
            descriptions_by_output_name={
                _chop(uid): default_description_fn(
                    manifest_dict[uid], display_raw_sql=len(output_unique_ids) < 500
                )
                for uid in output_unique_ids
            },
            can_subset=True,
        )

    return inner
