from enum import Enum
from typing import Any, Mapping, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions.events import AssetKey
from dagster._core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster._serdes.serdes import register_serdes_enum_fallbacks, whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo


@whitelist_for_serdes
class InstigatorType(Enum):
    SCHEDULE = "SCHEDULE"
    SENSOR = "SENSOR"


register_serdes_enum_fallbacks({"JobType": InstigatorType})
# for internal backcompat
JobType = InstigatorType


@whitelist_for_serdes
class SkipReason(NamedTuple("_SkipReason", [("skip_message", PublicAttr[Optional[str]])])):
    """
    Represents a skipped evaluation, where no runs are requested. May contain a message to indicate
    why no runs were requested.

    Attributes:
        skip_message (Optional[str]): A message displayed in dagit for why this evaluation resulted
            in no requested runs.
    """

    def __new__(cls, skip_message: Optional[str] = None):
        return super(SkipReason, cls).__new__(
            cls,
            skip_message=check.opt_str_param(skip_message, "skip_message"),
        )


@whitelist_for_serdes
class RunRequest(
    NamedTuple(
        "_RunRequest",
        [
            ("run_key", PublicAttr[Optional[str]]),
            ("run_config", PublicAttr[Mapping[str, Any]]),
            ("tags", PublicAttr[Mapping[str, str]]),
            ("job_name", PublicAttr[Optional[str]]),
            ("asset_selection", PublicAttr[Optional[Sequence[AssetKey]]]),
        ],
    )
):
    """
    Represents all the information required to launch a single run.  Must be returned by a
    SensorDefinition or ScheduleDefinition's evaluation function for a run to be launched.

    To build a run request for a particular partitition, use
    :py:func:`~JobDefinition.run_request_for_partition`.

    Attributes:
        run_key (Optional[str]): A string key to identify this launched run. For sensors, ensures that
            only one run is created per run key across all sensor evaluations.  For schedules,
            ensures that one run is created per tick, across failure recoveries. Passing in a `None`
            value means that a run will always be launched per evaluation.
        run_config (Optional[Dict]): The config that parameterizes the run execution to
            be launched, as a dict.
        tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the launched run.
        job_name (Optional[str]): (Experimental) The name of the job this run request will launch.
            Required for sensors that target multiple jobs.
        asset_selection (Optional[Sequence[AssetKey]]): A sequence of AssetKeys that should be
            launched with this run.
    """

    def __new__(
        cls,
        run_key: Optional[str] = None,
        run_config: Optional[Mapping[str, Any]] = None,
        tags: Optional[Mapping[str, str]] = None,
        job_name: Optional[str] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
    ):
        return super(RunRequest, cls).__new__(
            cls,
            run_key=check.opt_str_param(run_key, "run_key"),
            run_config=check.opt_dict_param(run_config, "run_config", key_type=str),
            tags=check.opt_dict_param(tags, "tags", key_type=str, value_type=str),
            job_name=check.opt_str_param(job_name, "job_name"),
            asset_selection=check.opt_nullable_sequence_param(
                asset_selection, "asset_selection", of_type=AssetKey
            ),
        )


@whitelist_for_serdes
class PipelineRunReaction(
    NamedTuple(
        "_PipelineRunReaction",
        [
            ("pipeline_run", Optional[PipelineRun]),
            ("error", Optional[SerializableErrorInfo]),
            ("run_status", Optional[PipelineRunStatus]),
        ],
    )
):
    """
    Represents a request that reacts to an existing pipeline run. If success, it will report logs
    back to the run.

    Attributes:
        pipeline_run (Optional[PipelineRun]): The pipeline run that originates this reaction.
        error (Optional[SerializableErrorInfo]): user code execution error.
        run_status: (Optional[PipelineRunStatus]): The run status that triggered the reaction.
    """

    def __new__(
        cls,
        pipeline_run: Optional[PipelineRun],
        error: Optional[SerializableErrorInfo] = None,
        run_status: Optional[PipelineRunStatus] = None,
    ):
        return super(PipelineRunReaction, cls).__new__(
            cls,
            pipeline_run=check.opt_inst_param(pipeline_run, "pipeline_run", PipelineRun),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            run_status=check.opt_inst_param(run_status, "run_status", PipelineRunStatus),
        )
