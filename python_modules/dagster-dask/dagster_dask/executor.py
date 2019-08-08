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
    return DaskConfig(**init_context.executor_config)
