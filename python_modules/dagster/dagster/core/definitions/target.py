from typing import List, NamedTuple, Optional, Union

from dagster import check

from .graph import GraphDefinition
from .pipeline import PipelineDefinition


class RepoRelativeTarget(NamedTuple):
    """
    The thing to be executed by a schedule or sensor, selecting by name a pipeline in the same repository.
    """

    pipeline_name: str
    mode: str
    solid_selection: Optional[List[str]]


class DirectTarget(NamedTuple("_DirectTarget", [("pipeline", PipelineDefinition)])):
    """
    The thing to be executed by a schedule or sensor, referenced directly and loaded
    in to any repository the container is included in.
    """

    def __new__(cls, graph: Union[GraphDefinition, PipelineDefinition]):
        check.inst_param(graph, "graph", (GraphDefinition, PipelineDefinition))

        # pipeline will become job / execution target
        if isinstance(graph, PipelineDefinition):
            pipeline = graph
        else:
            pipeline = graph.to_job(resource_defs={})

        check.invariant(
            len(pipeline.mode_definitions) == 1,
            f"Pipeline {pipeline.name} has more than one mode which makes it an invalid "
            "execution target.",
        )

        return super().__new__(
            cls,
            pipeline,
        )

    @property
    def pipeline_name(self) -> str:
        return self.pipeline.name

    @property
    def mode(self) -> str:
        return self.pipeline.mode_definitions[0].name

    @property
    def solid_selection(self):
        # open question on how to direct target subset pipeline
        return None

    def load(self):
        return self.pipeline
