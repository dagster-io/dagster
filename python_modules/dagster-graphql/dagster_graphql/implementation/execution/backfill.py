import pendulum
from dagster import check
from dagster.core.execution.backfill import (
    BulkActionStatus,
    PartitionBackfill,
    submit_backfill_runs,
)
from dagster.core.host_representation import RepositorySelector
from dagster.core.utils import make_new_backfill_id

from ..utils import capture_error


@capture_error
def create_and_launch_partition_backfill(graphene_info, backfill_params):
    from ...schema.backfill import GraphenePartitionBackfillSuccess
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

    partition_names = backfill_params.get("partitionNames")

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

    if not graphene_info.context.instance.has_bulk_actions_table() or backfill_params.get(
        "forceSynchronousSubmission"
    ):
        submitted_run_ids = submit_backfill_runs(graphene_info.context.instance, location, backfill)
        return GraphenePartitionBackfillSuccess(
            backfill_id=backfill_id, launched_run_ids=submitted_run_ids
        )
    else:
        graphene_info.context.instance.add_backfill(backfill)
        return GraphenePartitionBackfillSuccess(backfill_id=backfill_id)


@capture_error
def get_backfill(graphene_info, backfill_id):
    from ...schema.backfill import GraphenePartitionBackfill

    if graphene_info.context.instance.has_bulk_actions_table():
        backfill_job = graphene_info.context.instance.get_backfill(backfill_id)
        return GraphenePartitionBackfill(backfill_id, backfill_job)
    else:
        return GraphenePartitionBackfill(backfill_id)
