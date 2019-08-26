from collections import namedtuple

from dagster import check


class ScheduleDefinition(
    namedtuple('ScheduleDefinition', 'name cron_schedule execution_params environment_vars')
):
    '''Define a schedule that targets a repository

    Args:
        name (str): The name of the schedule.
        cron_schedule (str): The cron schedule for the schedule
        execution_params (dict): The execution params for the schedule
        environment_vars (dict): The environment variables to set for the schedule
    '''

    def __new__(cls, name, cron_schedule, execution_params, environment_vars=None):
        return super(ScheduleDefinition, cls).__new__(
            cls,
            check.str_param(name, 'name'),
            check.str_param(cron_schedule, 'cron_schedule'),
            check.dict_param(execution_params, 'execution_params'),
            check.opt_dict_param(environment_vars, 'environment_vars'),
        )
