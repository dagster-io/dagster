from collections import namedtuple

from dagster import check
from dagster.core.execution.config import ExecutorConfig


class DaskConfig(
    namedtuple('DaskConfig', 'cluster_type cluster_configuration'), ExecutorConfig,
):
    '''DaskConfig - configuration for the Dask execution engine

    Params:
        cluster_type (Optional[str]): The type of the cluster e.g., `local`, `yarn`.
        cluster_configuration (Optional[dict]): A dictionary of the cluster configuration.
    '''

    def __new__(
        cls, cluster_type, cluster_configuration,
    ):
        return super(DaskConfig, cls).__new__(
            cls,
            cluster_type=check.opt_str_param(cluster_type, 'cluster_type', default='local'),
            cluster_configuration=check.opt_dict_param(
                cluster_configuration, 'cluster_configuration'
            ),
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

        if self.cluster_type in ['yarn', 'kube', 'pbs']:
            dask_cfg = {'name': pipeline_name}
        else:
            dask_cfg = {}

        if self.cluster_configuration:
            for k, v in self.cluster_configuration.items():
                dask_cfg[k] = v

        # if address is set, don't add LocalCluster args
        # context: https://github.com/dask/distributed/issues/3313
        if (self.cluster_type == 'local') and ('address' not in dask_cfg):
            # We set threads_per_worker because Dagster is not thread-safe. Even though
            # environments=True by default, there is a clever piece of machinery
            # (dask.distributed.deploy.local.nprocesses_nthreads) that automagically makes execution
            # multithreaded by default when the number of available cores is greater than 4.
            # See: https://github.com/dagster-io/dagster/issues/2181
            # We may want to try to figure out a way to enforce this on remote Dask clusters against
            # which users run Dagster workloads.
            dask_cfg['threads_per_worker'] = 1

        return dask_cfg
