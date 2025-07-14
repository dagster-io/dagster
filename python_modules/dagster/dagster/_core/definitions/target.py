from collections.abc import Sequence
from typing import NamedTuple, Optional, Union

from typing_extensions import Self, TypeAlias

import dagster._check as check
from dagster._core.definitions.asset_selection import (
    AssetSelection,
    CoercibleToAssetSelection,
    is_coercible_to_asset_selection,
)
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import (
    UnresolvedAssetJobDefinition,
    define_asset_job,
)
from dagster._utils.warnings import deprecation_warning

ExecutableDefinition: TypeAlias = Union[
    JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition
]

CoercibleToAutomationTarget: TypeAlias = Union[
    CoercibleToAssetSelection,
    AssetsDefinition,
    ExecutableDefinition,
]

ResolvableToJob: TypeAlias = Union[JobDefinition, UnresolvedAssetJobDefinition, str]
"""
A piece of data that is resolvable to a JobDefinition. One of:

- JobDefinition
- UnresolvedAssetJobDefinition
- str (a job name)

The property of being resolvable to a JobDefinition is what unites all of the entities that an
AutomationTarget can wrap.
"""

ANONYMOUS_ASSET_JOB_PREFIX = "__anonymous_asset_job"


class AutomationTarget(
    NamedTuple(
        "_AutomationTarget",
        [
            ("resolvable_to_job", ResolvableToJob),
            ("op_selection", Optional[Sequence[str]]),
            ("assets_defs", Sequence[Union[AssetsDefinition, SourceAsset]]),
        ],
    )
):
    """An abstraction representing a job to be executed by an automation, i.e. schedule or sensor.

    Args:
        resolvable_to_job (ResolvableToJob): An entity that is resolvable to a job at
            definition-resolution time.
        op_selection (Optional[Sequence[str]]): An optional list of op names to execute within the job.
    """

    def __new__(
        cls,
        resolvable_to_job: Union[JobDefinition, UnresolvedAssetJobDefinition, str],
        op_selection: Optional[Sequence[str]] = None,
        assets_defs: Optional[Sequence[Union[AssetsDefinition, SourceAsset]]] = None,
    ):
        return super().__new__(
            cls,
            resolvable_to_job=check.inst_param(
                resolvable_to_job,
                "resolvable_to_job",
                (JobDefinition, UnresolvedAssetJobDefinition, str),
            ),
            op_selection=check.opt_nullable_sequence_param(
                op_selection, "op_selection", of_type=str
            ),
            assets_defs=check.opt_sequence_param(
                assets_defs, "assets_defs", of_type=AssetsDefinition
            ),
        )

    @classmethod
    def from_coercible(
        cls,
        coercible: CoercibleToAutomationTarget,
        automation_name: Optional[str] = None,  # only needed if we are generating an anonymous job
    ) -> Self:
        if isinstance(coercible, (JobDefinition, UnresolvedAssetJobDefinition)):
            return cls(coercible)
        elif isinstance(coercible, GraphDefinition):
            deprecation_warning(
                "Passing GraphDefinition as a job/target argument to ScheduleDefinition and SensorDefinition",
                breaking_version="2.0",
            )
            return cls(coercible.to_job())
        else:
            if isinstance(coercible, AssetsDefinition):
                asset_selection = AssetSelection.assets(coercible)
                assets_defs = [coercible]
            elif isinstance(coercible, AssetSelection):
                asset_selection = coercible
                assets_defs = []
            elif is_coercible_to_asset_selection(coercible):
                asset_selection = AssetSelection.from_coercible(coercible)
                assets_defs = (
                    [x for x in coercible if isinstance(x, (AssetsDefinition, SourceAsset))]
                    if isinstance(coercible, Sequence)
                    else []
                )
            else:
                check.failed(_make_invalid_target_error_message(coercible))

            job_name = _make_anonymous_asset_job_name(
                check.not_none(automation_name, "Must provide automation_name")
            )
            return cls(
                resolvable_to_job=define_asset_job(name=job_name, selection=asset_selection),
                assets_defs=assets_defs,
            )

    @property
    def job_name(self) -> str:
        if isinstance(self.resolvable_to_job, str):
            return self.resolvable_to_job
        else:
            return self.resolvable_to_job.name

    @property
    def job_def(self) -> Union[JobDefinition, UnresolvedAssetJobDefinition]:
        if isinstance(self.resolvable_to_job, str):
            check.failed(
                "Cannot access job_def for a target with string job name for resolvable_to_job"
            )
        return self.resolvable_to_job

    @property
    def has_job_def(self) -> bool:
        return isinstance(self.resolvable_to_job, (JobDefinition, UnresolvedAssetJobDefinition))


def _make_anonymous_asset_job_name(automation_name: str) -> str:
    return f"{ANONYMOUS_ASSET_JOB_PREFIX}_{automation_name}"


def _make_invalid_target_error_message(target: object) -> str:
    if isinstance(target, Sequence):
        additional_message = " If you pass a sequence to a schedule, it must be a sequence of strings, AssetKeys, AssetsDefinitions, or SourceAssets."
    else:
        additional_message = ""
    return f"Invalid target passed to schedule/sensor.{additional_message} Target: {target}"
