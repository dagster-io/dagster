from typing import TYPE_CHECKING, Union

import dagster._check as check
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun

from dagster_graphql.implementation.external import get_full_remote_job_or_raise
from dagster_graphql.implementation.utils import JobSubsetSelector, UserFacingGraphQLError
from dagster_graphql.schema.util import ResolveInfo

if TYPE_CHECKING:
    from dagster_graphql.schema.pipelines.pipeline_ref import GrapheneUnknownPipeline
    from dagster_graphql.schema.pipelines.snapshot import GraphenePipelineSnapshot


def get_job_snapshot_or_error_from_job_selector(
    graphene_info: ResolveInfo, job_selector: JobSubsetSelector
) -> "GraphenePipelineSnapshot":
    from dagster_graphql.schema.pipelines.snapshot import GraphenePipelineSnapshot

    check.inst_param(job_selector, "pipeline_selector", JobSubsetSelector)
    return GraphenePipelineSnapshot(get_full_remote_job_or_raise(graphene_info, job_selector))


def get_job_snapshot_or_error_from_snapshot_id(
    graphene_info: ResolveInfo, snapshot_id: str
) -> "GraphenePipelineSnapshot":
    check.str_param(snapshot_id, "snapshot_id")

    return _get_job_snapshot_from_instance(graphene_info.context.instance, snapshot_id)


def get_job_snapshot_or_error_from_snap_or_selector(
    graphene_info: ResolveInfo,
    job_selector: JobSubsetSelector,
    snapshot_id: str,
):
    from dagster_graphql.schema.pipelines.snapshot import GraphenePipelineSnapshot

    if graphene_info.context.instance.has_job_snapshot(snapshot_id):
        job_snapshot = graphene_info.context.instance.get_historical_job(snapshot_id)
        if job_snapshot:
            return GraphenePipelineSnapshot(job_snapshot)

    return get_job_snapshot_or_error_from_job_selector(graphene_info, job_selector)


# extracted this out to test
def _get_job_snapshot_from_instance(
    instance: DagsterInstance, snapshot_id: str
) -> "GraphenePipelineSnapshot":
    from dagster_graphql.schema.errors import GraphenePipelineSnapshotNotFoundError
    from dagster_graphql.schema.pipelines.snapshot import GraphenePipelineSnapshot

    if not instance.has_job_snapshot(snapshot_id):
        raise UserFacingGraphQLError(GraphenePipelineSnapshotNotFoundError(snapshot_id))

    historical_pipeline = instance.get_historical_job(snapshot_id)

    if not historical_pipeline:
        # Either a temporary error or it has been deleted in the interim
        raise UserFacingGraphQLError(GraphenePipelineSnapshotNotFoundError(snapshot_id))

    return GraphenePipelineSnapshot(historical_pipeline)


def get_job_reference_or_raise(
    graphene_info: ResolveInfo, dagster_run: DagsterRun
) -> Union["GraphenePipelineSnapshot", "GrapheneUnknownPipeline"]:
    """Returns a PipelineReference or raises a UserFacingGraphQLError if a pipeline
    reference cannot be retrieved based on the run, e.g, a UserFacingGraphQLError that wraps an
    InvalidSubsetError.
    """
    from dagster_graphql.schema.pipelines.pipeline_ref import GrapheneUnknownPipeline

    check.inst_param(dagster_run, "pipeline_run", DagsterRun)
    op_selection = (
        list(dagster_run.resolved_op_selection) if dagster_run.resolved_op_selection else None
    )

    if dagster_run.job_snapshot_id is None:
        return GrapheneUnknownPipeline(dagster_run.job_name, op_selection)

    return _get_job_snapshot_from_instance(
        graphene_info.context.instance, dagster_run.job_snapshot_id
    )
