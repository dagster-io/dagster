from dagster import Bool, Field, Int, String
from dagster.core.definitions.executor import executor

from .config import DaskConfig


@executor(
    name='dask',
    config={
        'address': Field(
            String,
            is_optional=True,
            description='The address of a `Scheduler` server, e.g., `\'127.0.0.1:8786\'`.',
        ),
        'timeout': Field(
            Int,
            is_optional=True,
            description='Timeout duration for initial connection to the scheduler.',
        ),
        'scheduler_file': Field(
            String,
            is_optional=True,
            description='Path to a file with scheduler information if available.',
        ),
        'direct_to_workers': Field(
            Bool,
            is_optional=True,
            description='Whether or not to connect directly to the workers, or to ask the '
            'scheduler to serve as intermediary.',
        ),
        'heartbeat_interval': Field(
            Int,
            is_optional=True,
            description='Time in milliseconds between heartbeats to scheduler.',
        ),
    },
)
def dask_executor(init_context):
    '''Dask-based executor.

    If the Dask executor is used without providing executor-specific config, a local Dask cluster
    will be created (as when calling :py:class:`dask.distributed.Client() <dask:distributed.Client>`
    without specifying the scheduler address).

    The Dask executor optionally takes the following config:

    .. code-block::

        {
            address?: '127.0.0.1:8786',  # The address of a Dask scheduler
            timeout?: 5,  # Timeout duration for initial connection to the scheduler
            scheduler_file?: '/path/to/file'  # Path to a file with scheduler information
            # Whether to connect directly to the workers, or ask the scheduler to serve as
            # intermediary
            direct_to_workers?: False,
            heartbeat_interval?: 1000,  # Time in milliseconds between heartbeats to scheduler
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

    return DaskConfig(**init_context.executor_config)
