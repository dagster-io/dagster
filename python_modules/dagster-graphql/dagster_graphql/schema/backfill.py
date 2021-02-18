import graphene

from .errors import (
    GrapheneInvalidOutputError,
    GrapheneInvalidStepError,
    GraphenePartitionSetNotFoundError,
    GraphenePipelineNotFoundError,
    GraphenePipelineRunConflict,
    GraphenePythonError,
    create_execution_params_error_types,
)
from .pipelines.config import GraphenePipelineConfigValidationInvalid
from .util import non_null_list

pipeline_execution_error_types = (
    GrapheneInvalidStepError,
    GrapheneInvalidOutputError,
    GraphenePipelineConfigValidationInvalid,
    GraphenePipelineNotFoundError,
    GraphenePipelineRunConflict,
    GraphenePythonError,
) + create_execution_params_error_types


class GraphenePartitionBackfillSuccess(graphene.ObjectType):
    backfill_id = graphene.NonNull(graphene.String)
    launched_run_ids = non_null_list(graphene.String)

    class Meta:
        name = "PartitionBackfillSuccess"


class GraphenePartitionBackfillResult(graphene.Union):
    class Meta:
        types = (
            GraphenePartitionBackfillSuccess,
            GraphenePartitionSetNotFoundError,
        ) + pipeline_execution_error_types
        name = "PartitionBackfillResult"
