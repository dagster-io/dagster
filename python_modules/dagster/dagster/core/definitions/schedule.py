from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.serdes import whitelist_for_serdes


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
        environment_dict (Optional[dict]): The enviroment configuration that parameterizes this
            execution, as a dict.
        should_execute (Optional[function]): Function that runs at schedule execution time that
            determines whether a schedule should execute. Defaults to a function that always returns
            ``True``.
        environment_vars (Optional[dict]): The environment variables to set for the schedule
    '''

    __slots__ = [
        '_schedule_definition_data',
        '_execution_params',
        '_environment_dict_fn',
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
        mode="default",
        should_execute=lambda: True,
        environment_vars=None,
    ):
        self._schedule_definition_data = ScheduleDefinitionData(
            name=check.str_param(name, 'name'),
            cron_schedule=check.str_param(cron_schedule, 'cron_schedule'),
            environment_vars=check.opt_dict_param(environment_vars, 'environment_vars'),
        )

        check.str_param(pipeline_name, 'pipeline_name')
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
        tags = check.opt_list_param(tags, 'tags')
        check.str_param(mode, 'mode')

        self._environment_dict_fn = check.opt_callable_param(
            environment_dict_fn, 'environment_dict_fn'
        )
        self._should_execute = check.callable_param(should_execute, 'should_execute')

        if self._environment_dict_fn and environment_dict:
            raise DagsterInvalidDefinitionError(
                'Attempted to provide both environment_dict_fn and environment_dict as arguments'
                ' to ScheduleDefinition. Must provide only one of the two.'
            )

        self._execution_params = {
            'environmentConfigData': environment_dict,
            'selector': {'name': pipeline_name},
            'executionMetadata': {"tags": tags},
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

    @property
    def environment_dict_fn(self):
        return self._environment_dict_fn

    @property
    def should_execute(self):
        return self._should_execute
