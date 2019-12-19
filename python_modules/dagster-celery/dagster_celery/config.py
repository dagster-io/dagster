import os
from collections import namedtuple

from dagster import check
from dagster.core.execution.config import (
    ExecutorConfig,
    check_non_ephemeral_instance,
    check_persistent_storage_requirement,
)

DEFAULT_PRIORITY = 5

DEFAULT_QUEUE = 'dagster'

DEFAULT_CONFIG = {
    # 'task_queue_max_priority': 10,
    'worker_prefetch_multiplier': 1,
}


class dict_wrapper(object):
    '''Wraps a dict to convert `obj['attr']` to `obj.attr`.'''

    def __init__(self, dictionary):
        self.__dict__ = dictionary


class CeleryConfig(
    namedtuple('CeleryConfig', 'broker backend include config_source'), ExecutorConfig,
):
    '''Configuration class for the Celery execution engine.

    Params:
        broker (Optional[str]): The URL of the Celery broker.
        backend (Optional[str]): The URL of the Celery backend.
        include (Optional[List[str]]): List of modules every worker should import.
        queues (Optional[List[Dict]]): 
        config_source (Optional[Dict]): Config settings for the Celery app.

    '''

    def __new__(
        cls, broker=None, backend='rpc://', include=None, config_source=None,
    ):
        return super(CeleryConfig, cls).__new__(
            cls,
            broker=check.opt_str_param(
                broker,
                'broker',
                default='pyamqp://guest@{hostname}'.format(
                    hostname=os.getenv('DAGSTER_CELERY_BROKER_HOST', 'localhost')
                ),
            ),
            backend=check.opt_str_param(backend, 'backend'),
            include=check.opt_list_param(include, 'include', of_type=str),
            config_source=dict_wrapper(
                dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, 'config_source'))
            ),
        )

    def check_requirements(self, instance, system_storage_def):
        check_non_ephemeral_instance(instance)
        check_persistent_storage_requirement(system_storage_def)

    @staticmethod
    def get_engine():
        from .engine import CeleryEngine

        return CeleryEngine()
