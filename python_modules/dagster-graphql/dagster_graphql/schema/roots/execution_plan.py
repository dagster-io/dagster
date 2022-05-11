# pylint: disable=missing-graphene-docstring
import graphene

from ..errors import GraphenePipelineNotFoundError, GraphenePythonError
from ..execution import GrapheneExecutionPlan
from ..pipelines.config import GrapheneRunConfigValidationInvalid
from ..pipelines.pipeline_errors import GrapheneInvalidSubsetError


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
