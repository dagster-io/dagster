from collections import namedtuple

from dagster import check
from dagster.core.execution.config import ExecutorConfig
from dagster.core.execution.retries import Retries, RetryMode

from .defaults import (
    broker_transport_options,
    broker_url,
    result_backend,
    task_default_priority,
    task_default_queue,
)

DEFAULT_CONFIG = {
    # 'task_queue_max_priority': 10,
    'worker_prefetch_multiplier': 1,
    'broker_transport_options': broker_transport_options,
    'task_default_priority': task_default_priority,
    'task_default_queue': task_default_queue,
}


class dict_wrapper(object):
    '''Wraps a dict to convert `obj['attr']` to `obj.attr`.'''

    def __init__(self, dictionary):
        self.__dict__ = dictionary


class CeleryConfig(
    namedtuple('CeleryConfig', 'broker backend include config_source retries'), ExecutorConfig,
):
    '''Configuration class for the Celery execution engine.

    Params:
        broker (Optional[str]): The URL of the Celery broker.
        backend (Optional[str]): The URL of the Celery backend.
        include (Optional[List[str]]): List of modules every worker should import.
        config_source (Optional[Dict]): Config settings for the Celery app.
        retries (Retries): Controls retry behavior
    '''

    def __new__(
        cls, retries, broker=None, backend=None, include=None, config_source=None,
    ):

        return super(CeleryConfig, cls).__new__(
            cls,
            broker=check.opt_str_param(broker, 'broker', default=broker_url),
            backend=check.opt_str_param(backend, 'backend', default=result_backend),
            include=check.opt_list_param(include, 'include', of_type=str),
            config_source=dict_wrapper(
                dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, 'config_source'))
            ),
            retries=check.inst_param(retries, 'retries', Retries),
        )

    @staticmethod
    def for_cli(broker=None, backend=None, include=None, config_source=None):
        return CeleryConfig(
            retries=Retries(RetryMode.DISABLED),
            broker=broker,
            backend=backend,
            include=include,
            config_source=config_source,
        )

    @staticmethod
    def get_engine():
        from .engine import CeleryEngine

        return CeleryEngine()
