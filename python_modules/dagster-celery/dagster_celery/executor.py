from dagster import Field, Permissive, String
from dagster.core.definitions.executor import check_cross_process_constraints, executor

from .config import CeleryConfig


@executor(
    name='celery',
    config={
        'broker': Field(
            String,
            is_required=False,
            description=(
                'The URL of the Celery broker. Default: '
                '\'pyamqp://guest@{os.getenv(\'DAGSTER_CELERY_BROKER_HOST\','
                '\'localhost\')}//\'.'
            ),
        ),
        'backend': Field(
            String,
            is_required=False,
            default_value='rpc://',
            description='The URL of the Celery results backend. Default: \'rpc://\'.',
        ),
        'include': Field(
            [str], is_required=False, description='List of modules every worker should import'
        ),
        'config_source': Field(
            Permissive(), is_required=False, description='Additional settings for the Celery app.'
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
    Redis instead of RabbitMQ). We expect that ``config_source`` will be less frequently
    modified, but that when solid executions are especially fast or slow, or when there are
    different requirements around idempotence or retry, it may make sense to execute pipelines
    with variations on these settings.

    If you'd like to configure a celery executor in addition to the
    :py:class:`~dagster.default_executors`, you should add it to the ``executor_defs`` defined on a
    :py:class:`~dagster.ModeDefinition` as follows:

    .. code-block:: python

        from dagster import ModeDefinition, default_executors, pipeline
        from dagster_celery import celery_executor

        @pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [celery_executor])])
        def celery_enabled_pipeline():
            pass

    Then you can configure the executor as follows:

    .. code-block:: YAML

        execution:
          celery:
            config:
              broker: 'pyamqp://guest@localhost//',  # Optional[str]: The URL of the Celery broker
              backend: 'rpc://', # Optional[str]: The URL of the Celery results backend
              include: ['my_module'], # Optional[List[str]]: Modules every worker should import
              config_source: # Dict[str, Any]: Any additional parameters to pass to the
                  ...        # Celery workers. This dict will be passed as the `config_source`
                             # argument of celery.Celery().

    Note that the YAML you provide here must align with the configuration with which the Celery
    workers on which you hope to run were started. If, for example, you point the executor at a
    different broker than the one your workers are listening to, the workers will never be able to
    pick up tasks for execution.
    '''
    check_cross_process_constraints(init_context)

    return CeleryConfig(**init_context.executor_config)
