import graphene

from ..errors import GraphenePythonError, GrapheneInvalidSubsetError, GraphenePipelineNotFoundError
from ..execution import GrapheneExecutionPlan
from ..pipelines.config import GrapheneRunConfigValidationInvalid


class GrapheneExecutionPlanOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneExecutionPlan,
            GrapheneRunConfigValidationInvalid,
            GraphenePipelineNotFoundError,
            GrapheneInvalidSubsetError,
            GraphenePythonError,
        )
        name = "ExecutionPlanOrError"
