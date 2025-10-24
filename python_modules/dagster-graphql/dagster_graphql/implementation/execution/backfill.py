from collections.abc import Sequence
from typing import TYPE_CHECKING, Union, cast

import dagster._check as check
from dagster._core.definitions.selector import (
    JobSelector,
    PartitionsByAssetSelector,
    RepositorySelector,
)
from dagster._core.definitions.utils import check_valid_title
from dagster._core.errors import DagsterInvariantViolationError, DagsterUserCodeProcessError
from dagster._core.events import AssetKey
from dagster._core.execution.asset_backfill import create_asset_backfill_data_from_asset_partitions
from dagster._core.execution.backfill import (
    BULK_ACTION_TERMINAL_STATUSES,
    BulkActionStatus,
    PartitionBackfill,
)
from dagster._core.execution.job_backfill import submit_backfill_runs
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.remote_representation.external_data import PartitionExecutionErrorSnap
from dagster._core.storage.tags import PARENT_BACKFILL_ID_TAG, ROOT_BACKFILL_ID_TAG
from dagster._core.utils import make_new_backfill_id
from dagster._core.workspace.permissions import Permissions
from dagster._time import datetime_from_timestamp, get_current_timestamp
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer
from dagster_shared.error import DagsterError

from dagster_graphql.implementation.utils import (
    AssetBackfillPreviewParams,
    BackfillParams,
    assert_permission_for_asset_graph,
    assert_permission_for_backfill,
    assert_permission_for_job,
    assert_permission_for_location,
    assert_valid_asset_partition_backfill,
    assert_valid_job_partition_backfill,
)

BACKFILL_CHUNK_SIZE = 25


if TYPE_CHECKING:
    from dagster_graphql.schema.backfill import (
        GrapheneAssetPartitions,
        GrapheneCancelBackfillSuccess,
        GrapheneLaunchBackfillSuccess,
        GrapheneResumeBackfillSuccess,
    )
    from dagster_graphql.schema.errors import GraphenePartitionSetNotFoundError
    from dagster_graphql.schema.util import ResolveInfo


def get_asset_backfill_preview(
    graphene_info: "ResolveInfo", backfill_preview_params: AssetBackfillPreviewParams
) -> Sequence["GrapheneAssetPartitions"]:
    from dagster_graphql.schema.backfill import GrapheneAssetPartitions

    asset_graph = graphene_info.context.asset_graph

    check.invariant(backfill_preview_params.get("assetSelection") is not None)
    check.invariant(backfill_preview_params.get("partitionNames") is not None)

    asset_selection = [
        cast("AssetKey", AssetKey.from_graphql_input(asset_key))
        for asset_key in backfill_preview_params["assetSelection"]
    ]
    partition_names: list[str] = backfill_preview_params["partitionNames"]

    asset_backfill_data = create_asset_backfill_data_from_asset_partitions(
        asset_graph, asset_selection, partition_names, graphene_info.context.instance
    )

    asset_partitions = []

    for asset_key in asset_backfill_data.get_targeted_asset_keys_topological_order(asset_graph):
        if asset_graph.get(asset_key).partitions_def:
            partitions_subset = asset_backfill_data.target_subset.partitions_subsets_by_asset_key[
                asset_key
            ]
            asset_partitions.append(
                GrapheneAssetPartitions(asset_key=asset_key, partitions_subset=partitions_subset)
            )
        else:
            asset_partitions.append(
                GrapheneAssetPartitions(asset_key=asset_key, partitions_subset=None)
            )

    return asset_partitions


def create_and_launch_partition_backfill(
    graphene_info: "ResolveInfo",
    backfill_params: BackfillParams,
) -> Union["GrapheneLaunchBackfillSuccess", "GraphenePartitionSetNotFoundError"]:
    from dagster_graphql.schema.backfill import GrapheneLaunchBackfillSuccess
    from dagster_graphql.schema.errors import GraphenePartitionSetNotFoundError
    from dagster_graphql.schema.runs import parse_run_config_input

    backfill_id = make_new_backfill_id()
    backfill_timestamp = get_current_timestamp()
    backfill_datetime = datetime_from_timestamp(backfill_timestamp)
    dynamic_partitions_store = CachingInstanceQueryer(
        instance=graphene_info.context.instance,
        asset_graph=graphene_info.context.asset_graph,
        loading_context=graphene_info.context,
        evaluation_time=backfill_datetime,
    )

    asset_selection = (
        [
            cast("AssetKey", AssetKey.from_graphql_input(asset_key))
            for asset_key in backfill_params["assetSelection"]
        ]
        if backfill_params.get("assetSelection")
        else None
    )

    partitions_by_assets = backfill_params.get("partitionsByAssets")

    if (
        asset_selection or backfill_params.get("selector") or backfill_params.get("partitionNames")
    ) and partitions_by_assets:
        raise DagsterInvariantViolationError(
            "partitions_by_assets cannot be used together with asset_selection, selector, or"
            " partitionNames"
        )

    tags = {t["key"]: t["value"] for t in backfill_params.get("tags", [])}

    tags = {**tags, **graphene_info.context.get_viewer_tags()}

    title = check_valid_title(backfill_params.get("title"))
    parsed_run_config = (
        parse_run_config_input(backfill_params["runConfigData"], raise_on_error=False)
        if "runConfigData" in backfill_params
        else None
    )
    run_config = parsed_run_config if isinstance(parsed_run_config, dict) else None

    if backfill_params.get("selector") is not None:  # job backfill
        partition_set_selector = backfill_params["selector"]
        partition_set_name = partition_set_selector.get("partitionSetName")
        repository_selector = RepositorySelector.from_graphql_input(
            partition_set_selector.get("repositorySelector")
        )
        partitions_sets = graphene_info.context.get_partition_sets(repository_selector)
        matches = [
            partition_set
            for partition_set in partitions_sets
            if partition_set.name == partition_set_selector.get("partitionSetName")
        ]
        if len(matches) != 1:
            # if no matches, either throw a not found error or a more general invariant violation
            # but, to maintain the same behavior, we should check location permissions first, which
            # got deferred to support per-definition permissions
            assert_permission_for_location(
                graphene_info,
                Permissions.LAUNCH_PARTITION_BACKFILL,
                repository_selector.location_name,
            )
            if not matches:
                return GraphenePartitionSetNotFoundError(partition_set_name)

            raise DagsterInvariantViolationError(
                f"Partition set names must be unique: found {len(matches)} matches for {partition_set_name}"
            )
        remote_partition_set = next(iter(matches))
        assert_permission_for_job(
            graphene_info,
            Permissions.LAUNCH_PARTITION_BACKFILL,
            JobSelector(
                location_name=repository_selector.location_name,
                repository_name=repository_selector.repository_name,
                job_name=remote_partition_set.job_name,
            ),
        )

        if backfill_params.get("allPartitions"):
            result = graphene_info.context.get_partition_names(
                repository_selector=repository_selector,
                job_name=remote_partition_set.job_name,
                instance=graphene_info.context.instance,
                selected_asset_keys=None,
            )
            if isinstance(result, PartitionExecutionErrorSnap):
                raise DagsterUserCodeProcessError.from_error_info(result.error)
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
            partition_set_origin=remote_partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_names,
            from_failure=bool(backfill_params.get("fromFailure")),
            reexecution_steps=backfill_params.get("reexecutionSteps"),
            tags=tags,
            backfill_timestamp=backfill_timestamp,
            asset_selection=asset_selection,
            title=title,
            description=backfill_params.get("description"),
            run_config=run_config,
        )
        assert_valid_job_partition_backfill(
            graphene_info,
            backfill,
            remote_partition_set.get_partitions_definition(),
            dynamic_partitions_store,
            backfill_datetime,
        )

        if backfill_params.get("forceSynchronousSubmission"):
            # should only be used in a test situation
            to_submit = [name for name in partition_names]
            submitted_run_ids: list[str] = []

            while to_submit:
                chunk = to_submit[:BACKFILL_CHUNK_SIZE]
                to_submit = to_submit[BACKFILL_CHUNK_SIZE:]
                submitted_run_ids.extend(
                    run_id
                    for run_id in submit_backfill_runs(
                        graphene_info.context.instance,
                        create_workspace=lambda: graphene_info.context,
                        backfill_job=backfill,
                        partition_names_or_ranges=chunk,
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

        asset_graph = graphene_info.context.asset_graph

        assert_permission_for_asset_graph(
            graphene_info, asset_graph, asset_selection, Permissions.LAUNCH_PARTITION_BACKFILL
        )

        backfill = PartitionBackfill.from_asset_partitions(
            backfill_id=backfill_id,
            asset_graph=asset_graph,
            backfill_timestamp=backfill_timestamp,
            tags=tags,
            asset_selection=asset_selection,
            partition_names=backfill_params.get("partitionNames"),
            dynamic_partitions_store=dynamic_partitions_store,
            all_partitions=backfill_params.get("allPartitions", False),
            title=title,
            description=backfill_params.get("description"),
            run_config=run_config,
        )
        assert_valid_asset_partition_backfill(
            graphene_info,
            backfill,
            backfill_datetime,
        )
    elif partitions_by_assets is not None:
        if backfill_params.get("forceSynchronousSubmission"):
            raise DagsterError(
                "forceSynchronousSubmission is not supported for pure asset backfills"
            )

        if backfill_params.get("fromFailure"):
            raise DagsterError("fromFailure is not supported for pure asset backfills")

        asset_graph = graphene_info.context.asset_graph

        partitions_by_assets = [
            PartitionsByAssetSelector.from_graphql_input(partitions_by_asset_selector)
            for partitions_by_asset_selector in partitions_by_assets
        ]

        selected_assets = list({selector.asset_key for selector in partitions_by_assets})

        assert_permission_for_asset_graph(
            graphene_info, asset_graph, selected_assets, Permissions.LAUNCH_PARTITION_BACKFILL
        )
        backfill = PartitionBackfill.from_partitions_by_assets(
            backfill_id=backfill_id,
            asset_graph=asset_graph,
            backfill_timestamp=backfill_timestamp,
            tags=tags,
            dynamic_partitions_store=dynamic_partitions_store,
            partitions_by_assets=partitions_by_assets,
            title=title,
            description=backfill_params.get("description"),
            run_config=run_config,
        )
        assert_valid_asset_partition_backfill(
            graphene_info,
            backfill,
            backfill_datetime,
        )

    else:
        raise DagsterError(
            "Backfill requested without specifying partition set selector or asset selection"
        )

    graphene_info.context.instance.add_backfill(backfill)
    return GrapheneLaunchBackfillSuccess(backfill_id=backfill_id)


def cancel_partition_backfill(
    graphene_info: "ResolveInfo", backfill_id: str
) -> "GrapheneCancelBackfillSuccess":
    from dagster_graphql.schema.backfill import GrapheneCancelBackfillSuccess

    backfill = graphene_info.context.instance.get_backfill(backfill_id)
    if not backfill:
        check.failed(f"No backfill found for id: {backfill_id}")

    assert_permission_for_backfill(graphene_info, Permissions.CANCEL_PARTITION_BACKFILL, backfill)

    graphene_info.context.instance.update_backfill(backfill.with_status(BulkActionStatus.CANCELING))

    return GrapheneCancelBackfillSuccess(backfill_id=backfill_id)


def resume_partition_backfill(
    graphene_info: "ResolveInfo", backfill_id: str
) -> "GrapheneResumeBackfillSuccess":
    from dagster_graphql.schema.backfill import GrapheneResumeBackfillSuccess

    backfill = graphene_info.context.instance.get_backfill(backfill_id)
    if not backfill:
        check.failed(f"No backfill found for id: {backfill_id}")

    assert_permission_for_backfill(graphene_info, Permissions.LAUNCH_PARTITION_BACKFILL, backfill)

    graphene_info.context.instance.update_backfill(backfill.with_status(BulkActionStatus.REQUESTED))
    return GrapheneResumeBackfillSuccess(backfill_id=backfill_id)


def retry_partition_backfill(
    graphene_info: "ResolveInfo", backfill_id: str, strategy: str
) -> "GrapheneLaunchBackfillSuccess":
    from dagster_graphql.schema.backfill import GrapheneLaunchBackfillSuccess

    backfill = graphene_info.context.instance.get_backfill(backfill_id)
    from_failure = ReexecutionStrategy(strategy) == ReexecutionStrategy.FROM_FAILURE
    if not backfill:
        check.failed(f"No backfill found for id: {backfill_id}")

    if backfill.status not in BULK_ACTION_TERMINAL_STATUSES:
        raise DagsterInvariantViolationError(
            f"Cannot re-execute backfill {backfill_id} because it is still in progress."
        )

    if backfill.is_asset_backfill:
        asset_backfill_data = backfill.get_asset_backfill_data(graphene_info.context.asset_graph)
        assets_to_request = asset_backfill_data.target_subset
        if from_failure:
            # determine the subset that should be retried by removing the successfully materialized subset from
            # the target subset. This ensures that if the backfill was canceled or marked failed that all
            # non-materialized asset partitions will be retried. asset_backfill_data.failed_and_downstream_asset
            # only contains asset partitions who's materialization runs failed and their downsteam assets, not
            # asset partitions that never got materialization runs.
            assets_to_request = assets_to_request - asset_backfill_data.materialized_subset
        if assets_to_request.num_partitions_and_non_partitioned_assets == 0:
            raise DagsterInvariantViolationError(
                "Cannot re-execute from failure an asset backfill that has no missing materializations."
            )

        assert_permission_for_backfill(
            graphene_info, Permissions.LAUNCH_PARTITION_BACKFILL, backfill
        )
        new_backfill = PartitionBackfill.from_asset_graph_subset(
            backfill_id=make_new_backfill_id(),
            asset_graph_subset=assets_to_request,
            dynamic_partitions_store=graphene_info.context.instance,
            tags={
                **backfill.tags,
                PARENT_BACKFILL_ID_TAG: backfill.backfill_id,
                ROOT_BACKFILL_ID_TAG: backfill.tags.get(ROOT_BACKFILL_ID_TAG, backfill.backfill_id),
            },
            backfill_timestamp=get_current_timestamp(),
            title=f"Re-execution of {backfill.title}" if backfill.title else None,
            description=backfill.description,
            run_config=backfill.run_config,
        )
    else:  # job backfill
        assert_permission_for_backfill(
            graphene_info, Permissions.LAUNCH_PARTITION_BACKFILL, backfill
        )

        new_backfill = PartitionBackfill(
            backfill_id=make_new_backfill_id(),
            partition_set_origin=backfill.partition_set_origin,
            status=BulkActionStatus.REQUESTED,
            partition_names=backfill.partition_names,
            from_failure=from_failure,
            reexecution_steps=backfill.reexecution_steps,
            tags={
                **backfill.tags,
                PARENT_BACKFILL_ID_TAG: backfill.backfill_id,
                ROOT_BACKFILL_ID_TAG: backfill.tags.get(ROOT_BACKFILL_ID_TAG, backfill.backfill_id),
            },
            backfill_timestamp=get_current_timestamp(),
            asset_selection=backfill.asset_selection,
            title=f"Re-execution of {backfill.title}" if backfill.title else None,
            description=backfill.description,
        )

    graphene_info.context.instance.add_backfill(new_backfill)
    return GrapheneLaunchBackfillSuccess(backfill_id=new_backfill.backfill_id)
