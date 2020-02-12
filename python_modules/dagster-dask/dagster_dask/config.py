from collections import namedtuple

from dagster import check
from dagster.core.execution.config import ExecutorConfig


class DaskConfig(
    namedtuple('DaskConfig', 'address timeout scheduler_file direct_to_workers heartbeat_interval'),
    ExecutorConfig,
):
    '''DaskConfig - configuration for the Dask execution engine

    Params:
        address (Optional[str]): The address of a `Scheduler` server, e.g., `'127.0.0.1:8786'`.
        timeout (Optional[int]): Timeout duration for initial connection to the scheduler.
        scheduler_file (Optional[str]): Path to a file with scheduler information if available.
        direct_to_workers (Optional[bool]): Whether or not to connect directly to the workers, or
            to ask the scheduler to serve as intermediary.
        heartbeat_interval (Optional[int]): Time in milliseconds between heartbeats to scheduler.
    '''

    def __new__(
        cls,
        address=None,
        timeout=None,
        scheduler_file=None,
        direct_to_workers=False,
        heartbeat_interval=None,
    ):
        return super(DaskConfig, cls).__new__(
            cls,
            address=check.opt_str_param(address, 'address'),
            timeout=check.opt_int_param(timeout, 'timeout'),
            scheduler_file=check.opt_str_param(scheduler_file, 'scheduler_file'),
            direct_to_workers=check.opt_bool_param(direct_to_workers, 'direct_to_workers'),
            heartbeat_interval=check.opt_int_param(heartbeat_interval, 'heartbeat_interval'),
        )

    @staticmethod
    def get_engine():
        from .engine import DaskEngine

        return DaskEngine

    def build_dict(self, pipeline_name):
        '''Returns a dict we can use for kwargs passed to dask client instantiation.

        Intended to be used like:

        with dask.distributed.Client(**cfg.build_dict()) as client:
            << use client here >>

        '''
        dask_cfg = {'name': pipeline_name}
        for cfg_param in [
            'address',
            'timeout',
            'scheduler_file',
            'direct_to_workers',
            'heartbeat_interval',
        ]:
            cfg_value = getattr(self, cfg_param, None)
            if cfg_value:
                dask_cfg[cfg_param] = cfg_value
        return dask_cfg
