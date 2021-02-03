import json
import os

import docker.client
from dagster import (
    DagsterInstance,
    EventMetadataEntry,
    Executor,
    Field,
    StringSource,
    check,
    executor,
)
from dagster.cli.api import ExecuteStepArgs
from dagster.core.definitions.executor import check_cross_process_constraints
from dagster.core.events import EngineEventData
from dagster.core.execution.retries import Retries
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import pack_value, serialize_dagster_namedtuple, unpack_value
from dagster.utils import merge_dicts
from dagster_celery.config import DEFAULT_CONFIG, dict_wrapper
from dagster_celery.core_execution_loop import DELEGATE_MARKER, core_celery_execution_loop
from dagster_celery.defaults import broker_url, result_backend
from dagster_celery.executor import CELERY_CONFIG

CELERY_DOCKER_CONFIG_KEY = "celery-docker"


def celery_docker_config():
    additional_config = {
        "docker": Field(
            {
                "image": Field(
                    StringSource,
                    is_required=False,
                    description="The docker image to be used for step execution.",
                ),
                "registry": Field(
                    {
                        "url": Field(StringSource),
                        "username": Field(StringSource),
                        "password": Field(StringSource),
                    },
                    is_required=False,
                    description="Information for using a non local/public docker registry",
                ),
                "env_vars": Field(
                    [str],
                    is_required=False,
                    description="The list of environment variables names to forward from the celery worker in to the docker container",
                ),
                "network": Field(
                    str,
                    is_required=False,
                    description="Name of the network this container will be connected to at creation time",
                ),
            },
            is_required=True,
            description="The configuration for interacting with docker in the celery worker.",
        ),
    }

    cfg = merge_dicts(CELERY_CONFIG, additional_config)
    return cfg


@executor(name=CELERY_DOCKER_CONFIG_KEY, config_schema=celery_docker_config())
def celery_docker_executor(init_context):
    """Celery-based executor which launches tasks in docker containers.

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
        from dagster_celery_docker.executor import celery_docker_executor

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

              docker:
                image: 'my_repo.com/image_name:latest'
                registry:
                  url: 'my_repo.com'
                  username: 'my_user'
                  password: {env: 'DOCKER_PASSWORD'}
                env_vars: ["DAGSTER_HOME"] # environment vars to pass from celery worker to docker

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

    In deployments where the celery_k8s_job_executor is used all appropriate celery and dagster_celery
    commands must be invoked with the `-A dagster_celery_docker.app` argument.
    """
    check_cross_process_constraints(init_context)

    exc_cfg = init_context.executor_config

    return CeleryDockerExecutor(
        broker=exc_cfg.get("broker"),
        backend=exc_cfg.get("backend"),
        config_source=exc_cfg.get("config_source"),
        include=exc_cfg.get("include"),
        retries=Retries.from_config(exc_cfg.get("retries")),
        docker_config=exc_cfg.get("docker"),
    )


class CeleryDockerExecutor(Executor):
    def __init__(
        self,
        retries,
        docker_config,
        broker=None,
        backend=None,
        include=None,
        config_source=None,
    ):
        self._retries = check.inst_param(retries, "retries", Retries)
        self.broker = check.opt_str_param(broker, "broker", default=broker_url)
        self.backend = check.opt_str_param(backend, "backend", default=result_backend)
        self.include = check.opt_list_param(include, "include", of_type=str)
        self.config_source = dict_wrapper(
            dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, "config_source"))
        )
        self.docker_config = check.dict_param(docker_config, "docker_config")

    @property
    def retries(self):
        return self._retries

    def execute(self, pipeline_context, execution_plan):

        return core_celery_execution_loop(
            pipeline_context, execution_plan, step_execution_fn=_submit_task_docker
        )

    def app_args(self):
        return {
            "broker": self.broker,
            "backend": self.backend,
            "include": self.include,
            "config_source": self.config_source,
            "retries": self.retries,
        }


def _submit_task_docker(app, pipeline_context, step, queue, priority):
    execute_step_args = ExecuteStepArgs(
        pipeline_origin=pipeline_context.pipeline.get_python_origin(),
        pipeline_run_id=pipeline_context.pipeline_run.run_id,
        step_keys_to_execute=[step.key],
        instance_ref=pipeline_context.instance.get_ref(),
        retries_dict=pipeline_context.executor.retries.for_inner_plan().to_config(),
    )

    task = create_docker_task(app)
    task_signature = task.si(
        execute_step_args_packed=pack_value(execute_step_args),
        docker_config=pipeline_context.executor.docker_config,
    )
    return task_signature.apply_async(
        priority=priority,
        queue=queue,
        routing_key="{queue}.execute_step_docker".format(queue=queue),
    )


def create_docker_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name="execute_step_docker", **task_kwargs)
    def _execute_step_docker(
        self,
        execute_step_args_packed,
        docker_config,
    ):
        """Run step execution in a Docker container."""
        execute_step_args = unpack_value(
            check.dict_param(
                execute_step_args_packed,
                "execute_step_args_packed",
            )
        )
        check.inst_param(execute_step_args, "execute_step_args", ExecuteStepArgs)

        check.dict_param(docker_config, "docker_config")

        instance = DagsterInstance.from_ref(execute_step_args.instance_ref)
        pipeline_run = instance.get_run_by_id(execute_step_args.pipeline_run_id)
        check.inst(
            pipeline_run,
            PipelineRun,
            "Could not load run {}".format(execute_step_args.pipeline_run_id),
        )
        step_keys_str = ", ".join(execute_step_args.step_keys_to_execute)

        input_json = serialize_dagster_namedtuple(execute_step_args)

        command = "dagster api execute_step {}".format(json.dumps(input_json))

        docker_image = (
            docker_config["image"]
            if docker_config.get("image")
            else execute_step_args.pipeline_origin.repository_origin.container_image
        )

        if not docker_image:
            raise Exception("No docker image specified by either the pipeline or the repository")

        client = docker.client.from_env()

        if docker_config.get("registry"):
            client.login(
                registry=docker_config["registry"]["url"],
                username=docker_config["registry"]["username"],
                password=docker_config["registry"]["password"],
            )

        # Post event for starting execution
        engine_event = instance.report_engine_event(
            "Executing steps {} in Docker container {}".format(step_keys_str, docker_image),
            pipeline_run,
            EngineEventData(
                [
                    EventMetadataEntry.text(step_keys_str, "Step keys"),
                    EventMetadataEntry.text(docker_image, "Image"),
                    EventMetadataEntry.text(self.request.hostname, "Celery worker"),
                ],
                marker_end=DELEGATE_MARKER,
            ),
            CeleryDockerExecutor,
            step_key=execute_step_args.step_keys_to_execute[0],
        )

        serialized_events = [serialize_dagster_namedtuple(engine_event)]

        docker_env = {}
        if docker_config.get("env_vars"):
            docker_env = {env_name: os.getenv(env_name) for env_name in docker_config["env_vars"]}

        try:
            docker_response = client.containers.run(
                docker_image,
                command=command,
                detach=False,
                auto_remove=True,
                # pass through this worker's environment for things like AWS creds etc.
                environment=docker_env,
                network=docker_config.get("network", None),
            )

            res = docker_response.decode("utf-8")
        except docker.errors.ContainerError as err:
            instance.report_engine_event(
                "Failed to run steps {} in Docker container {}".format(step_keys_str, docker_image),
                pipeline_run,
                EngineEventData(
                    [
                        EventMetadataEntry.text(docker_image, "Job image"),
                        EventMetadataEntry.text(err.stderr, "Docker stderr"),
                    ],
                ),
                CeleryDockerExecutor,
                step_key=execute_step_args.step_keys_to_execute[0],
            )
            raise
        else:
            if res is None:
                raise Exception("No response from execute_step in CeleryDockerExecutor")

            serialized_events += [event for event in res.split("\n") if event]

        return serialized_events

    return _execute_step_docker
