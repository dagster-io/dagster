import os
from collections import namedtuple

from dagster import check
from dagster.core.execution.config import ExecutorConfig

DEFAULT_PRIORITY = 5

DEFAULT_QUEUE = 'dagster'

DEFAULT_CONFIG = {
    # 'task_queue_max_priority': 10,
    'worker_prefetch_multiplier': 1,
    'broker_transport_options': {
        # these defaults were lifted from examples - worth updating
        "max_retries": 3,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },
}

DEFAULT_BROKER = 'pyamqp://guest@{hostname}:5672//'.format(
    hostname=os.getenv('DAGSTER_CELERY_BROKER_HOST', 'localhost')
)


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
            broker=check.opt_str_param(broker, 'broker', default=DEFAULT_BROKER),
            backend=check.opt_str_param(backend, 'backend'),
            include=check.opt_list_param(include, 'include', of_type=str),
            config_source=dict_wrapper(
                dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, 'config_source'))
            ),
        )

    @staticmethod
    def get_engine():
        from .engine import CeleryEngine

        return CeleryEngine()
