from typing import TYPE_CHECKING, NamedTuple, Optional, Sequence, Union

from typing_extensions import TypeAlias

import dagster._check as check

from .job_definition import JobDefinition
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition

if TYPE_CHECKING:
    from .graph_definition import GraphDefinition

ExecutableDefinition: TypeAlias = Union[
    JobDefinition, "GraphDefinition", UnresolvedAssetJobDefinition
]


class RepoRelativeTarget(NamedTuple):
    """The thing to be executed by a schedule or sensor, selecting by name a job in the same repository."""

    job_name: str
    op_selection: Optional[Sequence[str]]


class DirectTarget(
    NamedTuple(
        "_DirectTarget",
        [("target", ExecutableDefinition)],
    )
):
    """The thing to be executed by a schedule or sensor, referenced directly and loaded
    in to any repository the container is included in.
    """

    def __new__(
        cls,
        target: ExecutableDefinition,
    ):
        from .graph_definition import GraphDefinition

        check.inst_param(
            target, "target", (GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition)
        )

        return super().__new__(
            cls,
            target,
        )

    @property
    def job_name(self) -> str:
        return self.target.name

    @property
    def op_selection(self):
        # open question on how to direct target subset job
        return None

    def load(self) -> ExecutableDefinition:
        return self.target
