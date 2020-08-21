import os

import docker.client
from dagster_celery.config import DEFAULT_CONFIG, dict_wrapper
from dagster_celery.core_execution_loop import DELEGATE_MARKER, core_celery_execution_loop
from dagster_celery.defaults import broker_url, result_backend
from dagster_celery.executor import CELERY_CONFIG
from dagster_graphql.client.mutations import handle_execute_plan_result, handle_execution_errors

from dagster import (
    DagsterInstance,
    EventMetadataEntry,
    Executor,
    Field,
    StringSource,
    check,
    executor,
    seven,
)
from dagster.core.definitions.executor import check_cross_process_constraints
from dagster.core.events import EngineEventData
from dagster.core.execution.retries import Retries
from dagster.core.host_representation.handle import IN_PROCESS_NAME
from dagster.core.instance import InstanceRef
from dagster.serdes import serialize_dagster_namedtuple
from dagster.seven import JSONDecodeError
from dagster.utils import merge_dicts

CELERY_DOCKER_CONFIG_KEY = "celery-docker"


def celery_docker_config():
    additional_config = {
        "docker": Field(
            {
                "image": Field(
                    StringSource,
                    is_required=True,
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
            },
            is_required=True,
            description="The configuration for interacting with docker in the celery worker.",
        ),
        "repo_location_name": Field(
            StringSource,
            is_required=False,
            default_value=IN_PROCESS_NAME,
            description="[temporary workaround] The repository location name to use for execution.",
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
        repo_location_name=exc_cfg.get("repo_location_name"),
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
        repo_location_name=None,
    ):
        self._retries = check.inst_param(retries, "retries", Retries)
        self.broker = check.opt_str_param(broker, "broker", default=broker_url)
        self.backend = check.opt_str_param(backend, "backend", default=result_backend)
        self.include = check.opt_list_param(include, "include", of_type=str)
        self.config_source = dict_wrapper(
            dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, "config_source"))
        )
        self.docker_config = check.dict_param(docker_config, "docker_config")
        self.repo_location_name = check.str_param(repo_location_name, "repo_location_name")

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
        _self,
        instance_ref_dict,
        step_keys,
        run_config,
        mode,
        repo_name,
        repo_location_name,
        run_id,
        docker_config,
    ):
        """Run step execution in a Docker container.
        """
        instance_ref = InstanceRef.from_dict(instance_ref_dict)
        instance = DagsterInstance.from_ref(instance_ref)
        pipeline_run = instance.get_run_by_id(run_id)
        check.invariant(pipeline_run, "Could not load run {}".format(run_id))

        step_keys_str = ", ".join(step_keys)

        variables = {
            "executionParams": {
                "runConfigData": run_config,
                "mode": mode,
                "selector": {
                    "repositoryLocationName": repo_location_name,
                    "repositoryName": repo_name,
                    "pipelineName": pipeline_run.pipeline_name,
                    "solidSelection": list(pipeline_run.solids_to_execute)
                    if pipeline_run.solids_to_execute
                    else None,
                },
                "executionMetadata": {"runId": run_id},
                "stepKeys": step_keys,
            }
        }

        command = "dagster-graphql -v '{variables}' -p executePlan".format(
            variables=seven.json.dumps(variables)
        )
        docker_image = docker_config["image"]
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
                ],
                marker_end=DELEGATE_MARKER,
            ),
            CeleryDockerExecutor,
            step_key=step_keys[0],
        )

        events = [engine_event]

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
            )
            res = seven.json.loads(docker_response)

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
                step_key=step_keys[0],
            )
            raise

        except JSONDecodeError:
            instance.report_engine_event(
                "Failed to parse response for steps {} from Docker container {}".format(
                    step_keys_str, docker_image
                ),
                pipeline_run,
                EngineEventData(
                    [
                        EventMetadataEntry.text(docker_image, "Job image"),
                        EventMetadataEntry.text(docker_response, "Docker Response"),
                    ],
                ),
                CeleryDockerExecutor,
                step_key=step_keys[0],
            )
            raise

        else:
            handle_execution_errors(res, "executePlan")
            step_events = handle_execute_plan_result(res)

        events += step_events

        serialized_events = [serialize_dagster_namedtuple(event) for event in events]
        return serialized_events

    return _execute_step_docker
