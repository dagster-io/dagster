from typing import TYPE_CHECKING, NamedTuple, Optional, Sequence, Union

from typing_extensions import TypeAlias

import dagster._check as check

from .mode import DEFAULT_MODE_NAME
from .pipeline_definition import PipelineDefinition
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition

if TYPE_CHECKING:
    from .graph_definition import GraphDefinition

ExecutableDefinition: TypeAlias = Union[
    PipelineDefinition, "GraphDefinition", UnresolvedAssetJobDefinition
]


class RepoRelativeTarget(NamedTuple):
    """
    The thing to be executed by a schedule or sensor, selecting by name a pipeline in the same repository.
    """

    pipeline_name: str
    mode: str
    solid_selection: Optional[Sequence[str]]


class DirectTarget(
    NamedTuple(
        "_DirectTarget",
        [("target", ExecutableDefinition)],
    )
):
    """
    The thing to be executed by a schedule or sensor, referenced directly and loaded
    in to any repository the container is included in.
    """

    def __new__(
        cls,
        target: ExecutableDefinition,
    ):
        from .graph_definition import GraphDefinition

        check.inst_param(
            target, "target", (GraphDefinition, PipelineDefinition, UnresolvedAssetJobDefinition)
        )

        if isinstance(target, PipelineDefinition) and not len(target.mode_definitions) == 1:
            check.failed(
                "Only graphs, jobs, and single-mode pipelines are valid "
                "execution targets from a schedule or sensor. Please see the "
                f"following guide to migrate your pipeline '{target.name}': "
                "https://docs.dagster.io/guides/dagster/graph_job_op#migrating-to-ops-jobs-and-graphs"
            )

        return super().__new__(
            cls,
            target,
        )

    @property
    def pipeline_name(self) -> str:
        return self.target.name

    @property
    def mode(self) -> str:
        return (
            self.target.mode_definitions[0].name
            if isinstance(self.target, PipelineDefinition)
            else DEFAULT_MODE_NAME
        )

    @property
    def solid_selection(self):
        # open question on how to direct target subset pipeline
        return None

    def load(self) -> ExecutableDefinition:
        return self.target
