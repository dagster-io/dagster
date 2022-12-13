from typing import TYPE_CHECKING, Any, List, Mapping, Union, cast

import dagster._check as check
import pendulum
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.errors import DagsterError
from dagster._core.events import AssetKey
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import submit_backfill_runs
from dagster._core.host_representation import RepositorySelector
from dagster._core.utils import make_new_backfill_id
from dagster._core.workspace.permissions import Permissions

from ..utils import assert_permission, assert_permission_for_location, capture_error

BACKFILL_CHUNK_SIZE = 25


if TYPE_CHECKING:
    from ...schema.backfill import GrapheneLaunchBackfillSuccess
    from ...schema.errors import GraphenePartitionSetNotFoundError


@capture_error
def create_and_launch_partition_backfill(
    graphene_info, backfill_params: Mapping[str, Any]
) -> Union["GrapheneLaunchBackfillSuccess", "GraphenePartitionSetNotFoundError"]:
    from ...schema.backfill import GrapheneLaunchBackfillSuccess
    from ...schema.errors import GraphenePartitionSetNotFoundError

    backfill_id = make_new_backfill_id()

    asset_selection = (
        [
            cast(AssetKey, AssetKey.from_graphql_input(asset_key))
            for asset_key in backfill_params["assetSelection"]
        ]
        if backfill_params.get("assetSelection")
        else None
    )

    tags = {t["key"]: t["value"] for t in backfill_params.get("tags", [])}
    backfill_timestamp = pendulum.now("UTC").timestamp()

    if backfill_params.get("selector") is not None:  # job backfill
        partition_set_selector = backfill_params["selector"]
        partition_set_name = partition_set_selector.get("partitionSetName")
        repository_selector = RepositorySelector.from_graphql_input(
            partition_set_selector.get("repositorySelector")
        )
        assert_permission_for_location(
            graphene_info, Permissions.LAUNCH_PARTITION_BACKFILL, repository_selector.location_name
        )
        location = graphene_info.context.get_repository_location(repository_selector.location_name)

        repository = location.get_repository(repository_selector.repository_name)
        matches = [
            partition_set
            for partition_set in repository.get_external_partition_sets()
            if partition_set.name == partition_set_selector.get("partitionSetName")
        ]
        if not matches:
            return GraphenePartitionSetNotFoundError(partition_set_name)

        check.invariant(
            len(matches) == 1,
            "Partition set names must be unique: found {num} matches for {partition_set_name}"
            .format(num=len(matches), partition_set_name=partition_set_name),
        )
        external_partition_set = next(iter(matches))

        if backfill_params.get("allPartitions"):
            result = graphene_info.context.get_external_partition_names(external_partition_set)
            partition_names = result.partition_names
        elif backfill_params.get("partitionNames"):
            partition_names = backfill_params["partitionNames"]
        else:
            raise DagsterError(
                'Backfill requested without specifying either "allPartitions" or "partitionNames" '
                "arguments"
            )

        backfill = PartitionBackfill(
            backfill_id=backfill_id,
            partition_set_origin=external_partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_names,
            from_failure=bool(backfill_params.get("fromFailure")),
            reexecution_steps=backfill_params.get("reexecutionSteps"),
            tags=tags,
            backfill_timestamp=backfill_timestamp,
            asset_selection=asset_selection,
        )

        if backfill_params.get("forceSynchronousSubmission"):
            # should only be used in a test situation
            to_submit = [name for name in partition_names]
            submitted_run_ids: List[str] = []

            while to_submit:
                chunk = to_submit[:BACKFILL_CHUNK_SIZE]
                to_submit = to_submit[BACKFILL_CHUNK_SIZE:]
                submitted_run_ids.extend(
                    run_id
                    for run_id in submit_backfill_runs(
                        graphene_info.context.instance,
                        workspace=graphene_info.context,
                        repo_location=location,
                        backfill_job=backfill,
                        partition_names=chunk,
                    )
                    if run_id is not None
                )
            return GrapheneLaunchBackfillSuccess(
                backfill_id=backfill_id, launched_run_ids=submitted_run_ids
            )
    elif asset_selection is not None:  # pure asset backfill
        if backfill_params.get("forceSynchronousSubmission"):
            raise DagsterError(
                "forceSynchronousSubmission is not supported for pure asset backfills"
            )

        if backfill_params.get("fromFailure"):
            raise DagsterError("fromFailure is not supported for pure asset backfills")

        if backfill_params.get("allPartitions"):
            raise DagsterError("allPartitions is not supported for pure asset backfills")

        asset_graph = ExternalAssetGraph.from_workspace(graphene_info.context)

        location_names = set(
            repo_handle.repository_location_origin.location_name
            for repo_handle in asset_graph.repository_handles_by_key.values()
        )

        if not location_names:
            assert_permission(
                graphene_info,
                Permissions.LAUNCH_PARTITION_BACKFILL,
            )
        else:
            for location_name in location_names:
                assert_permission_for_location(
                    graphene_info, Permissions.LAUNCH_PARTITION_BACKFILL, location_name
                )

        backfill = PartitionBackfill.from_asset_partitions(
            asset_graph=asset_graph,
            backfill_id=backfill_id,
            tags=tags,
            backfill_timestamp=backfill_timestamp,
            asset_selection=asset_selection,
            partition_names=backfill_params["partitionNames"],
        )
    else:
        raise DagsterError(
            "Backfill requested without specifying partition set selector or asset selection"
        )

    graphene_info.context.instance.add_backfill(backfill)
    return GrapheneLaunchBackfillSuccess(backfill_id=backfill_id)


@capture_error
def cancel_partition_backfill(graphene_info, backfill_id):
    from ...schema.backfill import GrapheneCancelBackfillSuccess

    backfill = graphene_info.context.instance.get_backfill(backfill_id)
    if not backfill:
        check.failed(f"No backfill found for id: {backfill_id}")

    location_name = backfill.partition_set_origin.selector.location_name
    assert_permission_for_location(
        graphene_info, Permissions.CANCEL_PARTITION_BACKFILL, location_name
    )

    graphene_info.context.instance.update_backfill(backfill.with_status(BulkActionStatus.CANCELED))
    return GrapheneCancelBackfillSuccess(backfill_id=backfill_id)


@capture_error
def resume_partition_backfill(graphene_info, backfill_id):
    from ...schema.backfill import GrapheneResumeBackfillSuccess

    backfill = graphene_info.context.instance.get_backfill(backfill_id)
    if not backfill:
        check.failed(f"No backfill found for id: {backfill_id}")

    location_name = backfill.partition_set_origin.selector.location_name
    assert_permission_for_location(
        graphene_info, Permissions.LAUNCH_PARTITION_BACKFILL, location_name
    )

    graphene_info.context.instance.update_backfill(backfill.with_status(BulkActionStatus.REQUESTED))
    return GrapheneResumeBackfillSuccess(backfill_id=backfill_id)
