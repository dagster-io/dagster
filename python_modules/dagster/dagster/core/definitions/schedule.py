from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.instance import DagsterInstance
from dagster.core.serdes import whitelist_for_serdes

from .mode import DEFAULT_MODE_NAME


class ScheduleExecutionContext:
    ''' Defines the context where an instance is configured to execute scheduled jobs '''

    def __init__(self, instance):
        self._instance = check.inst_param(instance, 'instance', DagsterInstance)

    @property
    def instance(self):
        return self._instance


@whitelist_for_serdes
class ScheduleDefinitionData(
    namedtuple('ScheduleDefinitionData', 'name cron_schedule environment_vars')
):
    def __new__(cls, name, cron_schedule, environment_vars=None):
        return super(ScheduleDefinitionData, cls).__new__(
            cls,
            check.str_param(name, 'name'),
            check.str_param(cron_schedule, 'cron_schedule'),
            check.opt_dict_param(environment_vars, 'environment_vars'),
        )


class ScheduleDefinition(object):
    '''Define a schedule that targets a pipeline

    Args:
        name (str): The name of the schedule.
        cron_schedule (str): A valid cron string for the schedule
        pipeline_name (str): The name of the pipeline definition
        environment_dict (Optional[dict]): (deprecated) The environment config that parameterizes
            this execution, as a dict.
        environment_dict_fn (Callable[ScheduleExecutionContext, [Dict]]): A function that takes a
            ScheduleExecutionContext object and returns the environment configuration that
            parameterizes this execution, as a dict.
        tags (Optional[dict[str, str]]]): (deprecated) A dictionary of tags (key value pairs) that
            will be added to the generated run.
        tags_fn (Callable[ScheduleExecutionContext, Optional[dict[str, str]]]): A function that
            takes a ScheduleExecutionContext object and returns a dictionary of tags (key value
            pairs) that will be added to the generated run.
        solid_subset (Optional[List[str]]): The list of names of solid invocations (i.e., of
            unaliased solids or of their aliases if aliased) to execute with this schedule.
        mode (Optional[str]): The mode to apply when executing this schedule. (default: 'default')
        should_execute (Optional[Callable[ScheduleExecutionContext, bool]]): Function that takes a
            ScheduleExecutionContext object and runs at schedule execution time that determines
            whether a schedule should execute. Defaults to a function that always returns ``True``.
        environment_vars (Optional[dict[str, str]]): The environment variables to set for the
            schedule
    '''

    __slots__ = [
        '_schedule_definition_data',
        '_execution_params',
        '_environment_dict_fn',
        '_environment_dict',
        '_tags',
        '_tags_fn',
        '_should_execute',
    ]

    def __init__(
        self,
        name,
        cron_schedule,
        pipeline_name,
        environment_dict=None,
        environment_dict_fn=None,
        tags=None,
        tags_fn=None,
        solid_subset=None,
        mode="default",
        should_execute=None,
        environment_vars=None,
    ):
        check.str_param(name, 'name')
        check.str_param(cron_schedule, 'cron_schedule')
        check.str_param(pipeline_name, 'pipeline_name')
        check.opt_dict_param(environment_dict, 'environment_dict')
        check.opt_callable_param(environment_dict_fn, 'environment_dict_fn')
        check.opt_dict_param(tags, 'tags', key_type=str, value_type=str)
        check.opt_callable_param(tags_fn, 'tags_fn')
        check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str)
        mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)
        check.opt_callable_param(should_execute, 'should_execute')
        check.opt_dict_param(environment_vars, 'environment_vars', key_type=str, value_type=str)

        if environment_dict_fn and environment_dict:
            raise DagsterInvalidDefinitionError(
                'Attempted to provide both environment_dict_fn and environment_dict as arguments'
                ' to ScheduleDefinition. Must provide only one of the two.'
            )

        if tags_fn and tags:
            raise DagsterInvalidDefinitionError(
                'Attempted to provide both tags_fn and tags as arguments'
                ' to ScheduleDefinition. Must provide only one of the two.'
            )

        if not environment_dict and not environment_dict_fn:
            environment_dict_fn = lambda _context: {}

        if not tags and not tags_fn:
            tags_fn = lambda _context: {}

        if not should_execute:
            should_execute = lambda _context: True

        self._schedule_definition_data = ScheduleDefinitionData(
            name=check.str_param(name, 'name'),
            cron_schedule=check.str_param(cron_schedule, 'cron_schedule'),
            environment_vars=check.opt_dict_param(environment_vars, 'environment_vars'),
        )

        self._environment_dict = environment_dict
        self._environment_dict_fn = environment_dict_fn
        self._tags = tags
        self._tags_fn = tags_fn
        self._should_execute = should_execute
        self._execution_params = {
            'environmentConfigData': {},
            'selector': {'name': pipeline_name},
            'executionMetadata': {"tags": []},
            'mode': mode,
        }

    @property
    def schedule_definition_data(self):
        return self._schedule_definition_data

    @property
    def name(self):
        return self._schedule_definition_data.name

    @property
    def cron_schedule(self):
        return self._schedule_definition_data.cron_schedule

    @property
    def environment_vars(self):
        return self._schedule_definition_data.environment_vars

    @property
    def execution_params(self):
        return self._execution_params

    def get_environment_dict(self, context):
        check.inst_param(context, 'context', ScheduleExecutionContext)
        if self._environment_dict:
            return self._environment_dict
        return self._environment_dict_fn(context)

    def get_tags(self, context):
        check.inst_param(context, 'context', ScheduleExecutionContext)
        if self._tags:
            return self._tags
        return self._tags_fn(context)

    def should_execute(self, context):
        check.inst_param(context, 'context', ScheduleExecutionContext)
        return self._should_execute(context)
