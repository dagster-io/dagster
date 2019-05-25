import re

from collections import namedtuple

from dagster import check


class DaskConfig(
    namedtuple('DaskConfig', 'address timeout scheduler_file direct_to_workers heartbeat_interval')
):
    '''DaskConfig - configuration for the Dask execution engine
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
            # The address of a ``Scheduler`` server like a string '127.0.0.1:8786'
            address=check.opt_str_param(address, 'address'),
            # Timeout duration for initial connection to the scheduler
            timeout=check.opt_int_param(timeout, 'timeout'),
            # Path to a file with scheduler information if available
            scheduler_file=check.opt_str_param(scheduler_file, 'scheduler_file'),
            # Whether or not to connect directly to the workers, or to ask the scheduler to serve as
            # intermediary.
            direct_to_workers=check.opt_bool_param(direct_to_workers, 'direct_to_workers'),
            # Time in milliseconds between heartbeats to scheduler
            heartbeat_interval=check.opt_int_param(heartbeat_interval, 'heartbeat_interval'),
        )

    @property
    def is_remote_execution(self):
        return self.address and not re.match(r'127\.0\.0\.1|0\.0\.0\.0|localhost', self.address)

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
