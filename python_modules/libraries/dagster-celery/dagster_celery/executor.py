from dagster import Executor, Field, Noneable, Permissive, StringSource
from dagster import _check as check
from dagster import executor, multiple_process_executor_requirements
from dagster.core.execution.retries import RetryMode, get_retries_config
from dagster.grpc.types import ExecuteStepArgs
from dagster.serdes import pack_value

from .config import DEFAULT_CONFIG, dict_wrapper
from .defaults import broker_url, result_backend

CELERY_CONFIG = {
    "broker": Field(
        Noneable(StringSource),
        is_required=False,
        description=(
            "The URL of the Celery broker. Default: "
            "'pyamqp://guest@{os.getenv('DAGSTER_CELERY_BROKER_HOST',"
            "'localhost')}//'."
        ),
    ),
    "backend": Field(
        Noneable(StringSource),
        is_required=False,
        default_value="rpc://",
        description="The URL of the Celery results backend. Default: 'rpc://'.",
    ),
    "include": Field(
        [str], is_required=False, description="List of modules every worker should import"
    ),
    "config_source": Field(
        Noneable(Permissive()),
        is_required=False,
        description="Additional settings for the Celery app.",
    ),
    "retries": get_retries_config(),
}


@executor(
    name="celery",
    config_schema=CELERY_CONFIG,
    requirements=multiple_process_executor_requirements(),
)
def celery_executor(init_context):
    """Celery-based executor.

    The Celery executor exposes config settings for the underlying Celery app under
    the ``config_source`` key. This config corresponds to the "new lowercase settings" introduced
    in Celery version 4.0 and the object constructed from config will be passed to the
    :py:class:`celery.Celery` constructor as its ``config_source`` argument.
    (See https://docs.celeryq.dev/en/stable/userguide/configuration.html for details.)

    The executor also exposes the ``broker``, `backend`, and ``include`` arguments to the
    :py:class:`celery.Celery` constructor.

    In the most common case, you may want to modify the ``broker`` and ``backend`` (e.g., to use
    Redis instead of RabbitMQ). We expect that ``config_source`` will be less frequently
    modified, but that when solid executions are especially fast or slow, or when there are
    different requirements around idempotence or retry, it may make sense to execute jobs
    with variations on these settings.

    To use the `celery_executor`, set it as the `executor_def` when defining a job:

    .. code-block:: python

        from dagster import job
        from dagster_celery import celery_executor

        @job(executor_def=celery_executor)
        def celery_enabled_job():
            pass

    Then you can configure the executor as follows:

    .. code-block:: YAML

        execution:
          config:
            broker: 'pyamqp://guest@localhost//'  # Optional[str]: The URL of the Celery broker
            backend: 'rpc://' # Optional[str]: The URL of the Celery results backend
            include: ['my_module'] # Optional[List[str]]: Modules every worker should import
            config_source: # Dict[str, Any]: Any additional parameters to pass to the
                #...       # Celery workers. This dict will be passed as the `config_source`
                #...       # argument of celery.Celery().

    Note that the YAML you provide here must align with the configuration with which the Celery
    workers on which you hope to run were started. If, for example, you point the executor at a
    different broker than the one your workers are listening to, the workers will never be able to
    pick up tasks for execution.
    """

    return CeleryExecutor(
        broker=init_context.executor_config.get("broker"),
        backend=init_context.executor_config.get("backend"),
        config_source=init_context.executor_config.get("config_source"),
        include=init_context.executor_config.get("include"),
        retries=RetryMode.from_config(init_context.executor_config["retries"]),
    )


def _submit_task(app, plan_context, step, queue, priority, known_state):
    from .tasks import create_task

    execute_step_args = ExecuteStepArgs(
        pipeline_origin=plan_context.reconstructable_pipeline.get_python_origin(),
        pipeline_run_id=plan_context.pipeline_run.run_id,
        step_keys_to_execute=[step.key],
        instance_ref=plan_context.instance.get_ref(),
        retry_mode=plan_context.executor.retries.for_inner_plan(),
        known_state=known_state,
    )

    task = create_task(app)
    task_signature = task.si(
        execute_step_args_packed=pack_value(execute_step_args),
        executable_dict=plan_context.reconstructable_pipeline.to_dict(),
    )
    return task_signature.apply_async(
        priority=priority,
        queue=queue,
        routing_key="{queue}.execute_plan".format(queue=queue),
    )


class CeleryExecutor(Executor):
    def __init__(
        self,
        retries,
        broker=None,
        backend=None,
        include=None,
        config_source=None,
    ):
        self.broker = check.opt_str_param(broker, "broker", default=broker_url)
        self.backend = check.opt_str_param(backend, "backend", default=result_backend)
        self.include = check.opt_list_param(include, "include", of_type=str)
        self.config_source = dict_wrapper(
            dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, "config_source"))
        )
        self._retries = check.inst_param(retries, "retries", RetryMode)

    @property
    def retries(self):
        return self._retries

    def execute(self, plan_context, execution_plan):
        from .core_execution_loop import core_celery_execution_loop

        return core_celery_execution_loop(
            plan_context, execution_plan, step_execution_fn=_submit_task
        )

    @staticmethod
    def for_cli(broker=None, backend=None, include=None, config_source=None):
        return CeleryExecutor(
            retries=RetryMode(RetryMode.DISABLED),
            broker=broker,
            backend=backend,
            include=include,
            config_source=config_source,
        )

    def app_args(self):
        return {
            "broker": self.broker,
            "backend": self.backend,
            "include": self.include,
            "config_source": self.config_source,
            "retries": self.retries,
        }
