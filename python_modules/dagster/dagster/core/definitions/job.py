from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.serdes import whitelist_for_serdes

from .mode import DEFAULT_MODE_NAME
from .utils import check_valid_name


@whitelist_for_serdes
class JobType(Enum):
    SCHEDULE = "SCHEDULE"
    SENSOR = "SENSOR"


class JobContext:
    """Context for generating the execution parameters for an JobDefinition at runtime.

    An instance of this class is made available as the first argument to the JobDefinition
    functions: run_config_fn, tags_fn

    Attributes:
        instance (DagsterInstance): The instance configured to launch the job
    """

    __slots__ = ["_instance"]

    def __init__(self, instance):
        from dagster.core.instance import DagsterInstance

        self._instance = check.inst_param(instance, "instance", DagsterInstance)

    @property
    def instance(self):
        return self._instance


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
            cls, skip_message=check.opt_str_param(skip_message, "skip_message")
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


class JobDefinition:
    """Defines a job, which describes a series of runs for a particular pipeline.  These runs are
    grouped by job_name, using tags.

    Args:
        name (str): The name of this job.
        pipeline_name (str): The name of the pipeline to execute.
        mode (Optional[str]): The mode to apply when executing this pipeline. (default: 'default')
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute. e.g. ``['*some_solid+', 'other_solid']``
    """

    __slots__ = [
        "_name",
        "_job_type",
        "_pipeline_name",
        "_tags_fn",
        "_run_config_fn",
        "_mode",
        "_solid_selection",
    ]

    def __init__(
        self,
        name,
        job_type,
        pipeline_name,
        mode="default",
        solid_selection=None,
    ):
        self._name = check_valid_name(name)
        self._job_type = check.inst_param(job_type, "job_type", JobType)
        self._pipeline_name = check.str_param(pipeline_name, "pipeline_name")
        self._mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)
        self._solid_selection = check.opt_nullable_list_param(
            solid_selection, "solid_selection", of_type=str
        )

    @property
    def name(self):
        return self._name

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def job_type(self):
        return self._job_type

    @property
    def solid_selection(self):
        return self._solid_selection

    @property
    def mode(self):
        return self._mode
