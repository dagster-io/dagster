from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.tags import check_tags
from dagster.utils import merge_dicts

from .mode import DEFAULT_MODE_NAME


class ScheduleExecutionContext(namedtuple('ScheduleExecutionContext', 'instance')):
    '''Schedule-specific execution context.

    An instance of this class is made available as the first argument to various ScheduleDefinition
    functions. It is passed as the first argument to ``run_config_fn``, ``tags_fn``,
    and ``should_execute``.

    Attributes:
        instance (DagsterInstance): The instance configured to run the schedule
    '''

    def __new__(
        cls, instance,
    ):

        return super(ScheduleExecutionContext, cls).__new__(
            cls, check.inst_param(instance, 'instance', DagsterInstance),
        )


class ScheduleDefinition(object):
    '''Define a schedule that targets a pipeline

    Args:
        name (str): The name of the schedule to create.
        cron_schedule (str): A valid cron string specifying when the schedule will run, e.g.,
            '45 23 * * 6' for a schedule that runs at 11:45 PM every Saturday.
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        run_config (Optional[Dict]): The environment config that parameterizes this execution,
            as a dict.
        run_config_fn (Callable[[ScheduleExecutionContext], [Dict]]): A function that takes a
            ScheduleExecutionContext object and returns the environment configuration that
            parameterizes this execution, as a dict. You may set only one of ``run_config``
            and ``run_config_fn``.
        tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the scheduled runs.
        tags_fn (Optional[Callable[[ScheduleExecutionContext], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a dictionary of tags (string
            key-value pairs). You may set only one of ``tags`` and ``tags_fn``.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the schedule runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing this schedule. (default: 'default')
        should_execute (Optional[Callable[[ScheduleExecutionContext], bool]]): A function that runs
            at schedule execution time to determine whether a schedule should execute or skip. Takes
            a :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[dict[str, str]]): The environment variables to set for the
            schedule
    '''

    __slots__ = [
        '_name',
        '_cron_schedule',
        '_execution_params',
        '_run_config_fn',
        '_run_config',
        '_tags',
        '_mode',
        '_pipeline_name',
        '_solid_selection',
        '_tags_fn',
        '_should_execute',
        '_environment_vars',
    ]

    def __init__(
        self,
        name,
        cron_schedule,
        pipeline_name,
        run_config=None,
        run_config_fn=None,
        tags=None,
        tags_fn=None,
        solid_selection=None,
        mode="default",
        should_execute=None,
        environment_vars=None,
    ):

        self._name = check.str_param(name, 'name')
        self._cron_schedule = check.str_param(cron_schedule, 'cron_schedule')
        self._pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self._run_config = check.opt_dict_param(run_config, 'run_config')
        self._tags = check.opt_dict_param(tags, 'tags', key_type=str, value_type=str)

        check.opt_callable_param(tags_fn, 'tags_fn')
        self._solid_selection = check.opt_nullable_list_param(
            solid_selection, 'solid_selection', of_type=str
        )
        self._mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)
        check.opt_callable_param(should_execute, 'should_execute')
        self._environment_vars = check.opt_dict_param(
            environment_vars, 'environment_vars', key_type=str, value_type=str
        )

        if run_config_fn and run_config:
            raise DagsterInvalidDefinitionError(
                'Attempted to provide both run_config_fn and run_config as arguments'
                ' to ScheduleDefinition. Must provide only one of the two.'
            )

        if not run_config and not run_config_fn:
            run_config_fn = lambda _context: {}
        self._run_config_fn = run_config_fn

        if tags_fn and tags:
            raise DagsterInvalidDefinitionError(
                'Attempted to provide both tags_fn and tags as arguments'
                ' to ScheduleDefinition. Must provide only one of the two.'
            )

        if not tags and not tags_fn:
            tags_fn = lambda _context: {}
        self._tags_fn = tags_fn

        if not should_execute:
            should_execute = lambda _context: True
        self._should_execute = should_execute

    @property
    def name(self):
        return self._name

    @property
    def cron_schedule(self):
        return self._cron_schedule

    @property
    def environment_vars(self):
        return self._environment_vars

    @property
    def mode(self):
        return self._mode

    def get_run_config(self, context):
        check.inst_param(context, 'context', ScheduleExecutionContext)
        if self._run_config:
            return self._run_config
        return self._run_config_fn(context)

    def get_tags(self, context):
        check.inst_param(context, 'context', ScheduleExecutionContext)
        if self._tags:
            tags = self._tags
            check_tags(tags, 'tags')
        else:
            tags = self._tags_fn(context)
            # These tags are checked in _tags_fn_wrapper

        tags = merge_dicts(tags, PipelineRun.tags_for_schedule(self))

        return tags

    def should_execute(self, context):
        check.inst_param(context, 'context', ScheduleExecutionContext)
        return self._should_execute(context)

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def solid_selection(self):
        return self._solid_selection
