from dagster import Field, List, PermissiveDict, String
from dagster.core.definitions.executor import executor

from .config import CeleryConfig


@executor(
    name='celery',
    config={
        'broker': Field(
            String,
            is_optional=True,
            description=(
                'The URL of the Celery broker. Default: '
                '\'pyamqp://guest@{os.getenv(\'DAGSTER_CELERY_BROKER_HOST\','
                '\'localhost\')}//\'.'
            ),
        ),
        'backend': Field(
            String,
            is_optional=True,
            default_value='rpc://',
            description='The URL of the Celery results backend. Default: \'rpc://\'.',
        ),
        'include': Field(
            List[String], is_optional=True, description='List of modules every worker should import'
        ),
        'config_source': Field(
            PermissiveDict(), is_optional=True, description='Settings for the Celery app.'
        ),
    },
)
def celery_executor(init_context):
    '''Celery-based executor.

    The Celery executor exposes config settings for the underlying Celery app under
    the ``config_source`` key. This config corresponds to the "new lowercase settings" introduced
    in Celery version 4.0 and the object constructed from config will be passed to the
    :py:class:`celery.Celery` constructor as its ``config_source`` argument.
    (See https://docs.celeryproject.org/en/latest/userguide/configuration.html for details.)
    
    The executor also exposes the ``broker``, `backend`, and ``include`` arguments to the
    :py:class:`celery.Celery` constructor.

    In the most common case, you may want to modify the ``broker`` and ``backend`` (e.g., to use
    Redis  instead of RabbitMQ). We expect that ``celery_settings`` will be less frequently
    modified, but that when solid executions are especially fast or slow, or when there are
    different requirements around idempotence or retry, it will make sense to execute pipelines
    with variations on these settings.

    **Config**:
    .. code-block::

        {
            broker?: 'pyamqp://guest@localhost//',  # The URL of the Celery broker
            backend?: 'rpc://', # The URL of the Celery results backend
            include?: ['my_module'], # List of modules every worker should import
            celery_settings: {
                ... # Celery app config
            }
        }

    If you'd like to configure a celery executor in addition to the
    :py:class:`~dagster.default_executors`, you should add it to the ``executor_defs`` defined on a
    :py:class:`~dagster.ModeDefinition` as follows:

    .. code-block:: python

        from dagster import ModeDefinition, default_executors, pipeline
        from dagster_celery import celery_executor

        @pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [celery_executor])])
        def celery_enabled_pipeline():
            pass

    '''

    return CeleryConfig(**init_context.executor_config)
