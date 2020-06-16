from dagster import Field, Permissive, Selector
from dagster.core.definitions.executor import check_cross_process_constraints, executor

from .config import DaskConfig


@executor(
    name='dask',
    config_schema={
        'cluster': Field(
            Selector(
                {
                    'local': Field(
                        Permissive(), is_required=False, description='Local cluster configuration.'
                    ),
                    'yarn': Field(
                        Permissive(), is_required=False, description='YARN cluster configuration.'
                    ),
                    'ssh': Field(
                        Permissive(), is_required=False, description='SSH cluster configuration.'
                    ),
                    'pbs': Field(
                        Permissive(), is_required=False, description='PBS cluster configuration.'
                    ),
                    'kube': Field(
                        Permissive(),
                        is_required=False,
                        description='Kubernetes cluster configuration.',
                    ),
                }
            )
        )
    },
)
def dask_executor(init_context):
    '''Dask-based executor.

    If the Dask executor is used without providing executor-specific config, a local Dask cluster
    will be created (as when calling :py:class:`dask.distributed.Client() <dask:distributed.Client>`
    without specifying the scheduler address).

    The Dask executor optionally takes the following config:

    .. code-block:: none

        cluster:
            {
                local?:  # The cluster type, one of the following ('local', 'yarn', 'ssh', 'pbs', 'kube').
                    {
                        address?: '127.0.0.1:8786',  # The address of a Dask scheduler
                        timeout?: 5,  # Timeout duration for initial connection to the scheduler
                        scheduler_file?: '/path/to/file'  # Path to a file with scheduler information
                        # Whether to connect directly to the workers, or ask the scheduler to serve as
                        # intermediary
                        direct_to_workers?: False,
                        heartbeat_interval?: 1000,  # Time in milliseconds between heartbeats to scheduler
                    }
            }

    If you'd like to configure a dask executor in addition to the
    :py:class:`~dagster.default_executors`, you should add it to the ``executor_defs`` defined on a
    :py:class:`~dagster.ModeDefinition` as follows:

    .. code-block:: python

        from dagster import ModeDefinition, default_executors, pipeline
        from dagster_dask import dask_executor

        @pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])])
        def dask_enabled_pipeline():
            pass

    '''
    check_cross_process_constraints(init_context)
    ((cluster_type, cluster_configuration),) = init_context.executor_config['cluster'].items()
    return DaskConfig(cluster_type, cluster_configuration)
