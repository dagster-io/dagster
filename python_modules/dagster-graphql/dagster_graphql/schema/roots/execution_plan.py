import graphene

from ..errors import GraphenePipelineNotFoundError, GraphenePythonError
from ..execution import GrapheneExecutionPlan
from ..pipelines.config import GraphenePipelineConfigValidationInvalid
from ..pipelines.pipeline_errors import GrapheneInvalidSubsetError


class GrapheneExecutionPlanOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneExecutionPlan,
            GraphenePipelineConfigValidationInvalid,
            GraphenePipelineNotFoundError,
            GrapheneInvalidSubsetError,
            GraphenePythonError,
        )
        name = "ExecutionPlanOrError"
