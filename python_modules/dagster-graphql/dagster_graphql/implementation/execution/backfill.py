import pendulum

import dagster._check as check
from dagster.core.execution.backfill import (
    BulkActionStatus,
    PartitionBackfill,
    submit_backfill_runs,
)
from dagster.core.host_representation import RepositorySelector
from dagster.core.utils import make_new_backfill_id

from ..utils import capture_error

BACKFILL_CHUNK_SIZE = 25


@capture_error
def create_and_launch_partition_backfill(graphene_info, backfill_params):
    from ...schema.backfill import GrapheneLaunchBackfillSuccess
    from ...schema.errors import GraphenePartitionSetNotFoundError

    partition_set_selector = backfill_params.get("selector")
    partition_set_name = partition_set_selector.get("partitionSetName")
    repository_selector = RepositorySelector.from_graphql_input(
        partition_set_selector.get("repositorySelector")
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
        "Partition set names must be unique: found {num} matches for {partition_set_name}".format(
            num=len(matches), partition_set_name=partition_set_name
        ),
    )

    external_partition_set = next(iter(matches))

    if backfill_params.get("allPartitions"):
        result = graphene_info.context.get_external_partition_names(
            repository.handle, external_partition_set.name
        )
        partition_names = result.partition_names
    elif backfill_params.get("partitionNames"):
        partition_names = backfill_params.get("partitionNames")
    else:
        raise Exception(
            'Backfill requested without specifying either "allPartitions" or "partitionNames" '
            "arguments"
        )

    backfill_id = make_new_backfill_id()
    backfill = PartitionBackfill(
        backfill_id=backfill_id,
        partition_set_origin=external_partition_set.get_external_origin(),
        status=BulkActionStatus.REQUESTED,
        partition_names=partition_names,
        from_failure=bool(backfill_params.get("fromFailure")),
        reexecution_steps=backfill_params.get("reexecutionSteps"),
        tags={t["key"]: t["value"] for t in backfill_params.get("tags", [])},
        backfill_timestamp=pendulum.now("UTC").timestamp(),
    )

    if backfill_params.get("forceSynchronousSubmission"):
        # should only be used in a test situation
        to_submit = [name for name in partition_names]
        submitted_run_ids = []

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
                if run_id != None
            )
        return GrapheneLaunchBackfillSuccess(
            backfill_id=backfill_id, launched_run_ids=submitted_run_ids
        )

    graphene_info.context.instance.add_backfill(backfill)
    return GrapheneLaunchBackfillSuccess(backfill_id=backfill_id)


@capture_error
def cancel_partition_backfill(graphene_info, backfill_id):
    from ...schema.backfill import GrapheneCancelBackfillSuccess

    backfill = graphene_info.context.instance.get_backfill(backfill_id)
    if not backfill:
        check.failed(f"No backfill found for id: {backfill_id}")

    graphene_info.context.instance.update_backfill(backfill.with_status(BulkActionStatus.CANCELED))
    return GrapheneCancelBackfillSuccess(backfill_id=backfill_id)


@capture_error
def resume_partition_backfill(graphene_info, backfill_id):
    from ...schema.backfill import GrapheneResumeBackfillSuccess

    backfill = graphene_info.context.instance.get_backfill(backfill_id)
    if not backfill:
        check.failed(f"No backfill found for id: {backfill_id}")

    graphene_info.context.instance.update_backfill(backfill.with_status(BulkActionStatus.REQUESTED))
    return GrapheneResumeBackfillSuccess(backfill_id=backfill_id)
