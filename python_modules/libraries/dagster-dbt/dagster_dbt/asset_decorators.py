from functools import wraps
from typing import Any, Callable, Mapping, Optional, Set, cast

import dagster._check as check
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
from dagster._core.errors import DagsterInvalidSubsetError
from dbt.contracts.graph.manifest import WritableManifest

from dagster_dbt.asset_utils import (
    default_asset_key_fn,
    default_description_fn,
    default_freshness_policy_fn,
    default_group_fn,
    default_metadata_fn,
    get_deps,
)
from dagster_dbt.utils import input_name_fn, output_name_fn, select_unique_ids_from_manifest


class DbtExecutionContext(OpExecutionContext):
    """OpExecutionContext augmented with additional context related to dbt."""

    asset_key_fn: Callable[[Mapping[str, Any]], AssetKey]
    manifest_dict: Mapping[str, Any]

    def __init__(
        self,
        op_context: OpExecutionContext,
        asset_key_fn: Callable[[Mapping[str, Any]], AssetKey],
        raw_manifest_dict: Mapping[str, Mapping[str, Any]],
        base_select: str,
        base_exclude: Optional[str],
    ):
        super().__init__(op_context.get_step_execution_context())
        self.asset_key_fn = asset_key_fn
        self.manifest_dict = raw_manifest_dict
        self._fqn_by_output_name = {
            output_name_fn(node_info): ".".join(node_info["fqn"])
            for node_info in raw_manifest_dict["nodes"].values()
        }
        self._base_select = base_select
        self._base_exclude = base_exclude

    @property
    def all_selected(self) -> bool:
        return self.selected_output_names == len(self.op_def.output_defs)

    def get_dbt_selection_kwargs(self) -> Mapping[str, Any]:
        if self.all_selected:
            return {"select": self._base_select, "exclude": self._base_exclude}
        return {
            "select": " ".join(
                self._fqn_by_output_name[output_name] for output_name in self.selected_output_names
            )
        }


def dbt_assets(
    *,
    manifest_path: Optional[str],
    select: str = "*",
    exclude: str = "",
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
    config_schema: Optional[Any] = None,
    io_manager_key: Optional[str] = None,
    required_resource_keys: Optional[Set[str]] = None,
    _manifest_dict: Optional[Mapping[str, Any]] = None,
) -> Callable[..., AssetsDefinition]:
    if manifest_path is not None:
        manifest: WritableManifest = WritableManifest.read_and_check_versions(manifest_path)
        unique_ids = select_unique_ids_from_manifest(
            select=select, exclude=exclude, manifest_parsed=manifest
        )
        raw_manifest_dict = manifest.to_dict()
    else:
        _manifest_dict = check.not_none(_manifest_dict, "Must provide non-None manifest_path")
        unique_ids = select_unique_ids_from_manifest(
            select=select, exclude=exclude, manifest_json=_manifest_dict
        )
        raw_manifest_dict = _manifest_dict

    if len(unique_ids) == 0:
        raise DagsterInvalidSubsetError(f"No dbt models match the selection string '{select}'.")

    node_info_by_uid = {
        **raw_manifest_dict["nodes"],
        **raw_manifest_dict["sources"],
        **raw_manifest_dict["exposures"],
        **raw_manifest_dict["metrics"],
    }

    deps = get_deps(
        node_info_by_uid,
        selected_unique_ids=unique_ids,
        asset_resource_types=["model"] if models_only else ["model", "seed", "snapshot"],
    )
    output_unique_ids = set(deps.keys())
    input_unique_ids = set().union(*deps.values()) - output_unique_ids

    key_by_unique_id = {
        uid: asset_key_fn(node_info_by_uid[uid]) for uid in {*input_unique_ids, *output_unique_ids}
    }

    def inner(fn) -> AssetsDefinition:
        @op(
            name=op_name,
            tags={"kind": "dbt"},
            ins={input_name_fn(node_info_by_uid[uid]): In(Nothing) for uid in input_unique_ids},
            out={
                output_name_fn(node_info_by_uid[uid]): Out(
                    dagster_type=Nothing,
                    io_manager_key=io_manager_key,
                    is_required=False,
                )
                for uid in output_unique_ids
            },
            required_resource_keys=required_resource_keys,
            config_schema=config_schema,
        )
        @wraps(fn)
        def _op(*args, **kwargs):
            if is_context_provided(get_function_params(fn)):
                # convert the OpExecutionContext into a DbtExecutionContext, which has
                # additional context related to dbt
                yield from fn(
                    DbtExecutionContext(
                        cast(OpExecutionContext, args[0]),
                        asset_key_fn=asset_key_fn,
                        raw_manifest_dict=raw_manifest_dict,
                        base_select=select,
                        base_exclude=exclude,
                    ),
                    *args[1:],
                    **kwargs,
                )
            else:
                yield from fn(*args, **kwargs)

        return AssetsDefinition.from_op(
            _op,
            keys_by_input_name={
                input_name_fn(node_info_by_uid[uid]): key_by_unique_id[uid]
                for uid in input_unique_ids
            },
            keys_by_output_name={
                output_name_fn(node_info_by_uid[uid]): key_by_unique_id[uid]
                for uid in output_unique_ids
            },
            key_prefix=key_prefix,
            partitions_def=partitions_def,
            internal_asset_deps={
                output_name_fn(node_info_by_uid[uid]): {
                    key_by_unique_id[parent_uid] for parent_uid in parent_uids
                }
                for uid, parent_uids in deps.items()
            },
            metadata_by_output_name={
                output_name_fn(node_info_by_uid[uid]): metadata_fn(node_info_by_uid[uid])
                for uid in output_unique_ids
            },
            freshness_policies_by_output_name={
                output_name_fn(node_info_by_uid[uid]): freshness_policy_fn(node_info_by_uid[uid])
                for uid in output_unique_ids
            },
            group_names_by_output_name={
                output_name_fn(node_info_by_uid[uid]): group_fn(node_info_by_uid[uid])
                for uid in output_unique_ids
            },
            descriptions_by_output_name={
                output_name_fn(node_info_by_uid[uid]): default_description_fn(
                    node_info_by_uid[uid], display_raw_sql=len(output_unique_ids) < 500
                )
                for uid in output_unique_ids
            },
            can_subset=True,
        )

    return inner
