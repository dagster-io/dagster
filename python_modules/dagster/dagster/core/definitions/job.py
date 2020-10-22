from enum import Enum

from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.serdes import whitelist_for_serdes

from .mode import DEFAULT_MODE_NAME
from .utils import check_valid_name


@whitelist_for_serdes
class JobType(Enum):
    SCHEDULE = "SCHEDULE"
    SENSOR = "SENSOR"


class JobContext(object):
    """Context for generating the execution parameters for an JobDefinition at runtime.

    An instance of this class is made available as the first argument to the JobDefinition
    functions: run_config_fn, tags_fn

    Attributes:
        instance (DagsterInstance): The instance configured to launch the job
    """

    __slots__ = ["_instance"]

    def __init__(self, instance):
        self._instance = check.inst_param(instance, "instance", DagsterInstance)

    @property
    def instance(self):
        return self._instance


class JobDefinition(object):
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
        self, name, job_type, pipeline_name, mode="default", solid_selection=None,
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
