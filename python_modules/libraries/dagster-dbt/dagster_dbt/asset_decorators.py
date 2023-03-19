from functools import wraps
from typing import Any, Callable, Mapping, Optional, Set

from dagster import AssetsDefinition, In, Nothing, Out, op
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.metadata import MetadataUserInput
from dagster._core.definitions.partition import PartitionsDefinition
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
            return fn(*args, **kwargs)

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
