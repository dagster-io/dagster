from typing import NamedTuple, Optional, Sequence, Union

from typing_extensions import TypeAlias

import dagster._check as check

from .graph_definition import GraphDefinition
from .job_definition import JobDefinition
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition

ExecutableDefinition: TypeAlias = Union[
    JobDefinition, "GraphDefinition", UnresolvedAssetJobDefinition
]


ResolvableToJob: TypeAlias = Union[
    JobDefinition, UnresolvedAssetJobDefinition, GraphDefinition, str
]
"""
A piece of data that is resolvable to a JobDefinition. One of:

- JobDefinition
- UnresolvedAssetJobDefinition
- GraphDefinition
- str (a job name)

The property of being resolvable to a JobDefinition is what unites all of the entities that an
AutomationTarget can wrap.
"""


class AutomationTarget(
    NamedTuple(
        "_AutomationTarget",
        [
            ("resolvable_to_job", ResolvableToJob),
            ("op_selection", Optional[Sequence[str]]),
        ],
    )
):
    """An abstraction representing a job to be executed by an automation, i.e. schedule or sensor.

    Attributes:
        resolvable_to_job (ResolvableToJob): An entity that is resolvable to a job at
            definition-resolution time.
        op_selection (Optional[Sequence[str]]): An optional list of op names to execute within the job.
    """

    def __new__(
        cls,
        resolvable_to_job: Union[ExecutableDefinition, str],
        op_selection: Optional[Sequence[str]] = None,
    ):
        from .graph_definition import GraphDefinition

        check.inst_param(
            resolvable_to_job,
            "resolvable_to_job",
            (GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition, str),
        )

        return super().__new__(cls, resolvable_to_job, op_selection=op_selection)

    @property
    def job_name(self) -> str:
        if isinstance(self.resolvable_to_job, str):
            return self.resolvable_to_job
        else:
            return self.resolvable_to_job.name

    @property
    def executable_def(self) -> ExecutableDefinition:
        if isinstance(self.resolvable_to_job, str):
            check.failed(
                "Cannot access job_def for a target with string job name for resolvable_to_job"
            )
        return self.resolvable_to_job

    @property
    def has_executable_def(self) -> bool:
        return isinstance(
            self.resolvable_to_job, (GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition)
        )
