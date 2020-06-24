import os

from dagster import Executor, Field, StringSource, check, executor
from dagster.core.definitions.executor import check_cross_process_constraints
from dagster.core.execution.retries import Retries
from dagster.core.host_representation.handle import IN_PROCESS_NAME
from dagster.utils import merge_dicts

from .config import DEFAULT_CONFIG, dict_wrapper
from .defaults import broker_url, result_backend
from .executor import CELERY_CONFIG

CELERY_DOCKER_CONFIG_KEY = 'celery-docker'


def celery_docker_config():
    additional_config = {
        'docker_image': Field(
            StringSource,
            is_required=True,
            description='The docker image used for pipeline execution.',
        ),
        'repo_location_name': Field(
            StringSource,
            is_required=False,
            default_value=IN_PROCESS_NAME,
            description='The repository location name to use for execution.',
        ),
    }

    cfg = merge_dicts(CELERY_CONFIG, additional_config)
    return cfg


@executor(name=CELERY_DOCKER_CONFIG_KEY, config_schema=celery_docker_config())
def celery_docker_executor(init_context):
    '''Celery-based executor which launches tasks in docker containers.

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

    If you'd like to configure a Celery Docker executor in addition to the
    :py:class:`~dagster.default_executors`, you should add it to the ``executor_defs`` defined on a
    :py:class:`~dagster.ModeDefinition` as follows:

    .. code-block:: python

        from dagster import ModeDefinition, default_executors, pipeline
        from dagster_celery.executor_docker import celery_docker_executor

        @pipeline(mode_defs=[
            ModeDefinition(executor_defs=default_executors + [celery_docker_executor])
        ])
        def celery_enabled_pipeline():
            pass

    Then you can configure the executor as follows:

    .. code-block:: YAML

        execution:
          celery-docker:
            config:
              docker_image: 'my_repo.com/image_name:latest'
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

    If you want to use your private docker registry you have to pass your registry credentials
    through ENV as follows:

    .. code-block:: YAML

        DOCKER_USERNAME: my_user
        DOCKER_PASSWORD: my_secret_pass
        DOCKER_REGISTRY: my_repo.com

    '''
    check_cross_process_constraints(init_context)

    run_launcher = init_context.instance.run_launcher
    exc_cfg = init_context.executor_config

    docker_creds = {
        'username': os.environ.get('DOCKER_USERNAME'),
        'password': os.environ.get('DOCKER_PASSWORD'),
        'registry': os.environ.get('DOCKER_REGISTRY'),
    }

    return CeleryDockerExecutor(
        broker=exc_cfg.get('broker'),
        backend=exc_cfg.get('backend'),
        config_source=exc_cfg.get('config_source'),
        include=exc_cfg.get('include'),
        retries=Retries.from_config(exc_cfg.get('retries')),
        docker_image=exc_cfg.get('docker_image'),
        docker_creds=docker_creds,
        repo_location_name=exc_cfg.get('repo_location_name'),
    )


class CeleryDockerExecutor(Executor):
    def __init__(
        self,
        retries,
        broker=None,
        backend=None,
        include=None,
        config_source=None,
        docker_image=None,
        docker_creds=None,
        repo_location_name=None,
    ):
        self.retries = check.inst_param(retries, 'retries', Retries)
        self.broker = check.opt_str_param(broker, 'broker', default=broker_url)
        self.backend = check.opt_str_param(backend, 'backend', default=result_backend)
        self.include = check.opt_list_param(include, 'include', of_type=str)
        self.config_source = dict_wrapper(
            dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, 'config_source'))
        )
        self.docker_image = check.str_param(docker_image, 'docker_image')
        self.docker_creds = check.opt_dict_param(docker_creds, 'docker_creds')
        self.repo_location_name = check.str_param(repo_location_name, 'repo_location_name')

    def execute(self, pipeline_context, execution_plan):
        from .core_execution_loop import core_celery_execution_loop

        return core_celery_execution_loop(
            pipeline_context, execution_plan, step_execution_fn=_submit_task_docker
        )

    def app_args(self):
        return {
            'broker': self.broker,
            'backend': self.backend,
            'include': self.include,
            'config_source': self.config_source,
            'retries': self.retries,
        }


def _submit_task_docker(app, pipeline_context, step, queue, priority):
    from .tasks import create_docker_task

    task = create_docker_task(app)

    recon_repo = pipeline_context.pipeline.get_reconstructable_repository()

    task_signature = task.si(
        instance_ref_dict=pipeline_context.instance.get_ref().to_dict(),
        step_keys=[step.key],
        run_config=pipeline_context.pipeline_run.run_config,
        mode=pipeline_context.pipeline_run.mode,
        repo_name=recon_repo.get_definition().name,
        repo_location_name=pipeline_context.executor.repo_location_name,
        run_id=pipeline_context.pipeline_run.run_id,
        docker_image=pipeline_context.executor.docker_image,
        docker_creds=pipeline_context.executor.docker_creds,
    )
    return task_signature.apply_async(
        priority=priority,
        queue=queue,
        routing_key='{queue}.execute_step_docker'.format(queue=queue),
    )
