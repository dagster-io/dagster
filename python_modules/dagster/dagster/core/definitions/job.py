from collections import namedtuple

from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.utils.backcompat import experimental_class_warning

from .mode import DEFAULT_MODE_NAME


class JobContext(namedtuple("JobContext", "instance")):
    """Context for generating the execution parameters for an JobDefinition at runtime.

    An instance of this class is made available as the first argument to the JobDefinition
    functions: run_config_fn, tags_fn

    Attributes:
        instance (DagsterInstance): The instance configured to launch the job
    """

    def __new__(
        cls, instance,
    ):
        experimental_class_warning("JobContext")
        return super(JobContext, cls).__new__(
            cls, check.inst_param(instance, "instance", DagsterInstance),
        )


class JobDefinition(object):
    """Define a job, a named set of pipeline execution parameters that can be dynamically
    configured at runtime.

    Args:
        name (str): The name of this job.
        pipeline_name (str): The name of the pipeline to execute.
        run_config_fn (Callable[[JobContext], [Dict]]): A function that takes a
            JobContext object and returns the environment configuration that
            parameterizes this execution, as a dict.
        tags_fn (Optional[Callable[[JobContext], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the execution. Takes a
            :py:class:`~dagster.JobContext` and returns a dictionary of tags (string
            key-value pairs).
        mode (Optional[str]): The mode to apply when executing this pipeline. (default: 'default')
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute. e.g. ``['*some_solid+', 'other_solid']``
    """

    __slots__ = [
        "_name",
        "_pipeline_name",
        "_tags_fn",
        "_run_config_fn",
        "_mode",
        "_solid_selection",
    ]

    def __init__(
        self,
        name,
        pipeline_name,
        run_config_fn=None,
        tags_fn=None,
        mode="default",
        solid_selection=None,
    ):
        experimental_class_warning("JobDefinition")
        self._name = check.str_param(name, "name")
        self._pipeline_name = check.str_param(pipeline_name, "pipeline_name")
        self._run_config_fn = check.opt_callable_param(
            run_config_fn, "run_config_fn", lambda _context: {}
        )
        self._tags_fn = check.opt_callable_param(tags_fn, "tags_fn", lambda _context: {})
        self._mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)
        self._solid_selection = check.opt_nullable_list_param(
            solid_selection, "solid_selection", of_type=str
        )

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def solid_selection(self):
        return self._solid_selection

    @property
    def name(self):
        return self._name

    @property
    def mode(self):
        return self._mode

    def get_run_config(self, context):
        check.inst_param(context, "context", JobContext)
        return self._run_config_fn(context)

    def get_tags(self, context):
        check.inst_param(context, "context", JobContext)
        return self._tags_fn(context)
