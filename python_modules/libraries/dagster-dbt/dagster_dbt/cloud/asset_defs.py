from typing import Any, Callable, Dict, FrozenSet, Mapping, Optional, Sequence, Set, Tuple, cast

from dagster import AssetKey, AssetOut, AssetsDefinition, MetadataValue, ResourceDefinition
from dagster import _check as check
from dagster import multi_asset, with_resources
from dagster._annotations import experimental
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.metadata import MetadataUserInput
from dagster._core.execution.context.init import build_init_resource_context

from ..asset_defs import _get_asset_deps, _get_deps, _get_node_asset_key, _get_node_group_name
from ..utils import ASSET_RESOURCE_TYPES
from .resources import DbtCloudResourceV2


class DbtCloudCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(
        self,
        dbt_cloud_resource_def: ResourceDefinition,
        job_id: int,
        node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
        node_info_to_group_fn: Callable[[Dict[str, Any]], Optional[str]],
    ):
        self._dbt_cloud_resource_def = dbt_cloud_resource_def
        self._dbt_cloud: DbtCloudResourceV2 = dbt_cloud_resource_def(build_init_resource_context())
        self._job_id = job_id
        self._project_id: int
        self._has_generate_docs: bool
        self._node_info_to_asset_key = node_info_to_asset_key
        self._node_info_to_group_fn = node_info_to_group_fn

        super().__init__(unique_id=f"dbt-cloud-{job_id}")

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        dbt_nodes, dbt_dependencies = self._get_dbt_nodes_and_dependencies()
        return [self._build_dbt_cloud_assets_cacheable_data(dbt_nodes, dbt_dependencies)]

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        return with_resources(
            [
                self._build_dbt_cloud_assets_from_cacheable_data(assets_definition_metadata)
                for assets_definition_metadata in data
            ],
            {"dbt_cloud": self._dbt_cloud_resource_def},
        )

    def _get_dbt_nodes_and_dependencies(
        self,
    ) -> Tuple[Mapping[str, Any], Mapping[str, FrozenSet[str]]]:
        """
        For a given dbt Cloud job, fetch the latest run's dependency structure of executed nodes.
        """

        # Fetch information about the job.
        job = self._dbt_cloud.get_job(job_id=self._job_id)
        self._project_id = job["project_id"]
        self._has_generate_docs = job["generate_docs"]

        # Fetch the latest run for the job.
        runs = self._dbt_cloud.get_runs(job_id=self._job_id, order_by="-id", limit=1)

        # Assume that a run already exists for the job.
        #
        # In the future, we should be able to create a run for the job if one does not exist.
        # This can be done by triggering the job to run and then specifying a step override to
        # compile the dbt project.
        check.invariant(
            len(runs) == 1,
            (
                f"No runs found for the dbt Cloud job ({self._job_id}). "
                "The job must be run at least once in order to generate its assets. "
                "Run the job manually in dbt Cloud and try again."
            ),
        )

        # Fetch the latest run's manifest and run results.
        #
        # In the future, we should target the correct execution step, rather than assuming that
        # the last step is the one that we want.
        last_run_id = cast(int, runs[0]["id"])
        step = None

        manifest_json = self._dbt_cloud.get_manifest(run_id=last_run_id, step=step)
        run_results_json = self._dbt_cloud.get_run_results(run_id=last_run_id, step=step)

        # Filter the manifest to only include the nodes that were executed.
        dbt_nodes: Dict[str, Any] = {
            **manifest_json.get("nodes", {}),
            **manifest_json.get("sources", {}),
            **manifest_json.get("metrics", {}),
        }
        executed_node_ids: Set[str] = set(
            result["unique_id"] for result in run_results_json["results"]
        )

        dbt_dependencies = _get_deps(
            dbt_nodes=dbt_nodes,
            selected_unique_ids=executed_node_ids,
            asset_resource_types=ASSET_RESOURCE_TYPES,
        )

        return dbt_nodes, dbt_dependencies

    def _build_dbt_cloud_assets_cacheable_data(
        self, dbt_nodes: Mapping[str, Any], dbt_dependencies: Mapping[str, FrozenSet[str]]
    ) -> AssetsDefinitionCacheableData:
        """
        Given all of the nodes and dependencies for a dbt Cloud job, build the cacheable
        representation that generate the asset definition for the job.
        """

        (
            asset_deps,
            asset_ins,
            asset_outs,
            group_names_by_key,
            _,
            metadata_by_output_name,
        ) = _get_asset_deps(
            dbt_nodes=dbt_nodes,
            deps=dbt_dependencies,
            node_info_to_asset_key=self._node_info_to_asset_key,
            node_info_to_group_fn=self._node_info_to_group_fn,
            # In the future, allow the IO manager to be specified.
            io_manager_key=None,
            # We shouldn't display the raw sql. Instead, inspect if dbt docs were generated,
            # and attach metadata to link to the docs.
            display_raw_sql=False,
        )

        return AssetsDefinitionCacheableData(
            # In the future, we should allow additional upstream assets to be specified.
            keys_by_input_name={
                input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()
            },
            keys_by_output_name={
                output_name: asset_key for asset_key, (output_name, _) in asset_outs.items()
            },
            internal_asset_deps={
                asset_outs[asset_key][0]: asset_deps for asset_key, asset_deps in asset_deps.items()
            },
            # We don't rely on a static group name. Instead, we map over the dbt metadata to
            # determine the group name for each asset.
            group_name=None,
            metadata_by_output_name={
                output_name: self._build_dbt_cloud_assets_metadata(dbt_metadata)
                for output_name, dbt_metadata in metadata_by_output_name.items()
            },
            # In the future, we should allow the key prefix to be specified.
            key_prefix=None,
            # In the future, we should allow these assets to be subset, but this requires ad-hoc
            # overrides to the job's run/build step to materialize only the subset.
            can_subset=False,
            extra_metadata={
                "job_id": self._job_id,
                "group_names_by_output_name": {
                    asset_outs[asset_key][0]: group_name
                    for asset_key, group_name in group_names_by_key.items()
                },
            },
        )

    def _build_dbt_cloud_assets_metadata(self, dbt_metadata: Dict[str, Any]) -> MetadataUserInput:
        metadata = {
            "dbt Cloud Job": MetadataValue.url(
                self._dbt_cloud.build_url_for_job(
                    project_id=self._project_id,
                    job_id=self._job_id,
                )
            ),
        }

        if self._has_generate_docs:
            metadata["dbt Cloud Documentation"] = MetadataValue.url(
                self._dbt_cloud.build_url_for_cloud_docs(
                    job_id=self._job_id,
                    resource_type=dbt_metadata["resource_type"],
                    unique_id=dbt_metadata["unique_id"],
                )
            )

        return metadata

    def _build_dbt_cloud_assets_from_cacheable_data(
        self, assets_definition_cacheable_data: AssetsDefinitionCacheableData
    ) -> AssetsDefinition:
        metadata = cast(Mapping[str, Any], assets_definition_cacheable_data.extra_metadata)
        job_id = cast(int, metadata["job_id"])
        group_names_by_output_name = cast(Mapping[str, str], metadata["group_names_by_output_name"])

        @multi_asset(
            name=f"dbt_cloud_job_{job_id}",
            non_argument_deps=set(
                (assets_definition_cacheable_data.keys_by_input_name or {}).values()
            ),
            outs={
                output_name: AssetOut(
                    key=asset_key,
                    group_name=group_names_by_output_name.get(output_name),
                    metadata=(assets_definition_cacheable_data.metadata_by_output_name or {}).get(
                        output_name
                    ),
                )
                for output_name, asset_key in (
                    assets_definition_cacheable_data.keys_by_output_name or {}
                ).items()
            },
            internal_asset_deps={
                output_name: set(asset_deps)
                for output_name, asset_deps in (
                    assets_definition_cacheable_data.internal_asset_deps or {}
                ).items()
            },
            required_resource_keys={"dbt_cloud"},
            compute_kind="dbt",
        )
        def _assets(_context):
            # Defer implementation of the asset for now. For simplicity, we just want the
            # dependency structure of the dbt Cloud assets to be defined.
            pass

        return _assets


@experimental
def load_assets_from_dbt_cloud_job(
    dbt_cloud: ResourceDefinition,
    job_id: int,
) -> CacheableAssetsDefinition:
    """
    Loads a set of assets from a dbt Cloud job.

    Args:
        dbt_cloud (ResourceDefinition): The dbt Cloud resource to use to connect to the dbt Cloud API.
        job_id (int): The ID of the dbt Cloud job to load assets from.

    Returns:
        CacheableAssetsDefinition: A definition for the loaded assets.
    """

    return DbtCloudCacheableAssetsDefinition(
        dbt_cloud_resource_def=dbt_cloud,
        job_id=job_id,
        # In the future, allow arbitrary mappings to asset keys and groups from the dbt metadata.
        node_info_to_asset_key=_get_node_asset_key,
        node_info_to_group_fn=_get_node_group_name,
    )
