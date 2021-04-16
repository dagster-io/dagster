from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class JobType(Enum):
    SCHEDULE = "SCHEDULE"
    SENSOR = "SENSOR"


@whitelist_for_serdes
class SkipReason(namedtuple("_SkipReason", "skip_message")):
    """
    Represents a skipped evaluation, where no runs are requested. May contain a message to indicate
    why no runs were requested.

    Attributes:
        skip_message (Optional[str]): A message displayed in dagit for why this evaluation resulted
            in no requested runs.
    """

    def __new__(cls, skip_message=None):
        return super(SkipReason, cls).__new__(
            cls,
            skip_message=check.opt_str_param(skip_message, "skip_message"),
        )


@whitelist_for_serdes
class RunRequest(namedtuple("_RunRequest", "run_key run_config tags")):
    """
    Represents all the information required to launch a single run.  Must be returned by a
    SensorDefinition or ScheduleDefinition's evaluation function for a run to be launched.

    Attributes:
        run_key (str | None): A string key to identify this launched run. For sensors, ensures that
            only one run is created per run key across all sensor evaluations.  For schedules,
            ensures that one run is created per tick, across failure recoveries. Passing in a `None`
            value means that a run will always be launched per evaluation.
        run_config (Optional[Dict]): The environment config that parameterizes the run execution to
            be launched, as a dict.
        tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the launched run.
    """

    def __new__(cls, run_key, run_config=None, tags=None):
        return super(RunRequest, cls).__new__(
            cls,
            run_key=check.opt_str_param(run_key, "run_key"),
            run_config=check.opt_dict_param(run_config, "run_config"),
            tags=check.opt_dict_param(tags, "tags"),
        )


@whitelist_for_serdes
class PipelineRunReaction(namedtuple("_PipelineRunReaction", "pipeline_run error")):
    """
    Represents a request that reacts to an existing pipeline run. If success, it will report logs
    back to the run.

    Attributes:
        pipeline_run (PipelineRun): The pipeline run that originates this reaction.
        error (Optional[SerializableErrorInfo]): user code execution error.
    """

    def __new__(cls, pipeline_run, error=None):
        return super(PipelineRunReaction, cls).__new__(
            cls,
            pipeline_run=check.opt_inst_param(pipeline_run, "pipeline_run", PipelineRun),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )
