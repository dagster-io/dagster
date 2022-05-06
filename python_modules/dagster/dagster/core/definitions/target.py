from typing import TYPE_CHECKING, Dict, List, Mapping, NamedTuple, Optional, Union, cast

from dagster import check

from .graph_definition import GraphDefinition
from .resource_definition import ResourceDefinition

if TYPE_CHECKING:
    from .job_definition import JobDefinition, PendingJobDefinition
    from .pipeline_definition import PipelineDefinition


class RepoRelativeTarget(NamedTuple):
    """
    The thing to be executed by a schedule or sensor, selecting by name a pipeline in the same repository.
    """

    pipeline_name: str
    mode: str
    solid_selection: Optional[List[str]]


class DirectTarget(
    NamedTuple(
        "_DirectTarget",
        [("target", Union[GraphDefinition, "JobDefinition", "PendingJobDefinition"])],
    )
):
    """
    The thing to be executed by a schedule or sensor, referenced directly and loaded
    in to any repository the container is included in.
    """

    def __new__(cls, target: Union[GraphDefinition, "JobDefinition", "PendingJobDefinition"]):
        from .job_definition import JobDefinition, PendingJobDefinition

        check.inst_param(target, "target", (GraphDefinition, JobDefinition, PendingJobDefinition))

        return super().__new__(
            cls,
            target,
        )

    def load(self, resource_defs: Mapping[str, ResourceDefinition]) -> "PipelineDefinition":
        from .job_definition import PendingJobDefinition

        # Can probably memoize this.
        if isinstance(self.target, GraphDefinition):
            return self.target.to_job(
                resource_defs=cast(Dict[str, ResourceDefinition], resource_defs)
            )
        elif isinstance(self.target, PendingJobDefinition):
            return self.target.coerce_to_job_def(resource_defs=resource_defs)
        else:
            return self.target

    @property
    def pipeline_name(self) -> str:
        return self.target.name

    @property
    def pipeline(self) -> Union[GraphDefinition, "JobDefinition", "PendingJobDefinition"]:
        return self.target

    @property
    def mode(self) -> str:
        return "default"

    @property
    def solid_selection(self):
        # open question on how to direct target subset pipeline
        return None
