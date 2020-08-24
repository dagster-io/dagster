from collections import namedtuple

from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.utils.backcompat import experimental_class_warning

from .mode import DEFAULT_MODE_NAME


class TriggeredExecutionContext(namedtuple("TriggeredExecutionContext", "instance")):
    """Trigger-specific execution context.

    An instance of this class is made available as the first argument to the
    TriggeredExecutionDefinition execution_params_fn

    Attributes:
        instance (DagsterInstance): The instance configured to run the triggered execution
    """

    def __new__(
        cls, instance,
    ):
        experimental_class_warning("TriggeredExecutionContext")
        return super(TriggeredExecutionContext, cls).__new__(
            cls, check.inst_param(instance, "instance", DagsterInstance),
        )


class TriggeredExecutionDefinition(object):
    """Define a pipeline execution that responds to a trigger

    Args:
        name (str): The name of this triggered execution to create.
        pipeline_name (str): The name of the pipeline to execute when the trigger fires.
        run_config_fn (Callable[[TriggeredExecutionContext], [Dict]]): A function that takes a
            TriggeredExecutionContext object and returns the environment configuration that
            parameterizes this execution, as a dict.
        tags_fn (Optional[Callable[[TriggeredExecutionContext], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the triggered execution. Takes a
            :py:class:`~dagster.TriggeredExecutionContext` and returns a dictionary of tags (string
            key-value pairs).
        should_execute_fn (Optional[Callable[[TriggeredExecutionContext], bool]]): A function that
            runs at trigger time to determine whether a pipeline execution should be initiated or
            skipped. Takes a :py:class:`~dagster.TriggeredExecutionContext` and returns a boolean
            (``True`` if a pipeline run should be execute). Defaults to a function that always
            returns ``True``.
        mode (Optional[str]): The mode to apply when executing this pipeline. (default: 'default')
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the trigger fires. e.g. ``['*some_solid+', 'other_solid']``
    """

    __slots__ = [
        "_name",
        "_pipeline_name",
        "_tags_fn",
        "_run_config_fn",
        "_should_execute_fn",
        "_mode",
        "_solid_selection",
    ]

    def __init__(
        self,
        name,
        pipeline_name,
        run_config_fn=None,
        tags_fn=None,
        should_execute_fn=None,
        mode="default",
        solid_selection=None,
    ):
        experimental_class_warning("TriggeredExecutionDefinition")
        self._name = check.str_param(name, "name")
        self._pipeline_name = check.str_param(pipeline_name, "pipeline_name")
        self._run_config_fn = check.opt_callable_param(
            run_config_fn, "run_config_fn", lambda _context: {}
        )
        self._tags_fn = check.opt_callable_param(tags_fn, "tags_fn", lambda _context: {})
        self._should_execute_fn = check.opt_callable_param(
            should_execute_fn, "should_execute_fn", lambda _context: True
        )
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
        check.inst_param(context, "context", TriggeredExecutionContext)
        return self._run_config_fn(context)

    def get_tags(self, context):
        check.inst_param(context, "context", TriggeredExecutionContext)
        return self._tags_fn(context)

    def should_execute(self, context):
        check.inst_param(context, "context", TriggeredExecutionContext)
        return self._should_execute_fn(context)
