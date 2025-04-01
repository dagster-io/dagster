import os

import docker.client
from dagster import (
    DagsterInstance,
    Executor,
    Field,
    Permissive,
    StringSource,
    _check as check,
    executor,
    multiple_process_executor_requirements,
)
from dagster._cli.api import ExecuteStepArgs
from dagster._core.events import EngineEventData
from dagster._core.events.utils import filter_dagster_events_from_cli_logs
from dagster._core.execution.retries import RetryMode
from dagster._serdes import pack_value, serialize_value, unpack_value
from dagster._utils.merger import merge_dicts
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
                    description=(
                        "The list of environment variables names to forward from the celery worker"
                        " in to the docker container"
                    ),
                ),
                "network": Field(
                    str,
                    is_required=False,
                    description=(
                        "Name of the network this container will be connected to at creation time"
                    ),
                ),
                "container_kwargs": Field(
                    Permissive(),
                    is_required=False,
                    description="Additional keyword args for the docker container",
                ),
            },
            is_required=True,
            description="The configuration for interacting with docker in the celery worker.",
        ),
    }

    cfg = merge_dicts(CELERY_CONFIG, additional_config)
    return cfg


@executor(
    name=CELERY_DOCKER_CONFIG_KEY,
    config_schema=celery_docker_config(),
    requirements=multiple_process_executor_requirements(),
)
def celery_docker_executor(init_context):
    """Celery-based executor which launches tasks in docker containers.

    The Celery executor exposes config settings for the underlying Celery app under
    the ``config_source`` key. This config corresponds to the "new lowercase settings" introduced
    in Celery version 4.0 and the object constructed from config will be passed to the
    :py:class:`celery.Celery` constructor as its ``config_source`` argument.
    (See https://docs.celeryq.dev/en/stable/userguide/configuration.html for details.)

    The executor also exposes the ``broker``, `backend`, and ``include`` arguments to the
    :py:class:`celery.Celery` constructor.

    In the most common case, you may want to modify the ``broker`` and ``backend`` (e.g., to use
    Redis instead of RabbitMQ). We expect that ``config_source`` will be less frequently
    modified, but that when op executions are especially fast or slow, or when there are
    different requirements around idempotence or retry, it may make sense to execute jobs
    with variations on these settings.

    To use the `celery_docker_executor`, set it as the `executor_def` when defining a job:

    .. code-block:: python

        from dagster import job
        from dagster_celery_docker.executor import celery_docker_executor

        @job(executor_def=celery_docker_executor)
        def celery_enabled_job():
            pass

    Then you can configure the executor as follows:

    .. code-block:: YAML

        execution:
          config:
            docker:
              image: 'my_repo.com/image_name:latest'
              registry:
                url: 'my_repo.com'
                username: 'my_user'
                password: {env: 'DOCKER_PASSWORD'}
              env_vars: ["DAGSTER_HOME"] # environment vars to pass from celery worker to docker
              container_kwargs: # keyword args to be passed to the container. example:
                volumes: ['/home/user1/:/mnt/vol2','/var/www:/mnt/vol1']

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

    In deployments where the celery_docker_job_executor is used all appropriate celery and dagster_celery
    commands must be invoked with the `-A dagster_celery_docker.app` argument.
    """
    exc_cfg = init_context.executor_config

    return CeleryDockerExecutor(
        broker=exc_cfg.get("broker"),
        backend=exc_cfg.get("backend"),
        config_source=exc_cfg.get("config_source"),
        include=exc_cfg.get("include"),
        retries=RetryMode.from_config(exc_cfg.get("retries")),
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
        self._retries = check.inst_param(retries, "retries", RetryMode)
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

    def execute(self, plan_context, execution_plan):
        return core_celery_execution_loop(
            plan_context, execution_plan, step_execution_fn=_submit_task_docker
        )

    def app_args(self):
        return {
            "broker": self.broker,
            "backend": self.backend,
            "include": self.include,
            "config_source": self.config_source,
            "retries": self.retries,
        }


def _submit_task_docker(app, plan_context, step, queue, priority, known_state):
    execute_step_args = ExecuteStepArgs(
        job_origin=plan_context.reconstructable_job.get_python_origin(),
        run_id=plan_context.dagster_run.run_id,
        step_keys_to_execute=[step.key],
        instance_ref=plan_context.instance.get_ref(),
        retry_mode=plan_context.executor.retries.for_inner_plan(),
        known_state=known_state,
        print_serialized_events=True,
    )

    task = create_docker_task(app)
    task_signature = task.si(  # pyright: ignore[reportFunctionMemberAccess]
        execute_step_args_packed=pack_value(execute_step_args),
        docker_config=plan_context.executor.docker_config,
    )
    return task_signature.apply_async(
        priority=priority,
        queue=queue,
        routing_key=f"{queue}.execute_step_docker",
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
            ),
            as_type=ExecuteStepArgs,
        )

        check.dict_param(docker_config, "docker_config")

        instance = DagsterInstance.from_ref(execute_step_args.instance_ref)  # pyright: ignore[reportArgumentType]
        dagster_run = check.not_none(
            instance.get_run_by_id(execute_step_args.run_id),
            f"Could not load run {execute_step_args.run_id}",
        )
        step_keys_str = ", ".join(execute_step_args.step_keys_to_execute)  # pyright: ignore[reportCallIssue,reportArgumentType]

        docker_image = (
            docker_config["image"]
            if docker_config.get("image")
            else dagster_run.job_code_origin.repository_origin.container_image  # pyright: ignore[reportOptionalMemberAccess]
        )

        if not docker_image:
            raise Exception("No docker image specified by either the job or the repository")

        client = docker.client.from_env()

        if docker_config.get("registry"):
            client.login(
                registry=docker_config["registry"]["url"],
                username=docker_config["registry"]["username"],
                password=docker_config["registry"]["password"],
            )

        # Post event for starting execution
        engine_event = instance.report_engine_event(
            f"Executing steps {step_keys_str} in Docker container {docker_image}",
            dagster_run,
            EngineEventData(
                {
                    "Step keys": step_keys_str,
                    "Image": docker_image,
                    "Celery worker": self.request.hostname,
                },
                marker_end=DELEGATE_MARKER,
            ),
            CeleryDockerExecutor,
            step_key=execute_step_args.step_keys_to_execute[0],  # pyright: ignore[reportOptionalSubscript]
        )

        serialized_events = [serialize_value(engine_event)]

        docker_env = {}
        if docker_config.get("env_vars"):
            docker_env = {env_name: os.getenv(env_name) for env_name in docker_config["env_vars"]}

        container_kwargs = check.opt_dict_param(
            docker_config.get("container_kwargs"), "container_kwargs", key_type=str
        )

        # set defaults for detach and auto_remove
        container_kwargs["detach"] = container_kwargs.get("detach", False)
        container_kwargs["auto_remove"] = container_kwargs.get("auto_remove", True)

        # if environment variables are provided via container_kwargs, merge with env_vars
        if container_kwargs.get("environment") is not None:
            e_vars = container_kwargs.get("environment")
            if isinstance(e_vars, dict):
                docker_env.update(e_vars)
            else:
                for v in e_vars:  # pyright: ignore[reportOptionalIterable]
                    key, val = v.split("=")
                    docker_env[key] = val
            del container_kwargs["environment"]

        try:
            docker_response = client.containers.run(
                docker_image,
                command=execute_step_args.get_command_args(),  # type: ignore # Sequence list mismatch
                environment=docker_env,  # type: ignore # Mapping dict mismatch
                network=docker_config.get("network", None),
                **container_kwargs,
            )

            res = docker_response.decode("utf-8")
        except docker.errors.ContainerError as err:  # pyright: ignore[reportAttributeAccessIssue]
            metadata = {"Job image": docker_image}
            if err.stderr is not None:
                metadata["Docker stderr"] = err.stderr

            instance.report_engine_event(
                f"Failed to run steps {step_keys_str} in Docker container {docker_image}",
                dagster_run,
                EngineEventData(metadata),
                CeleryDockerExecutor,
                step_key=execute_step_args.step_keys_to_execute[0],  # pyright: ignore[reportOptionalSubscript]
            )
            raise
        else:
            if res is None:
                raise Exception("No response from execute_step in CeleryDockerExecutor")

            events = filter_dagster_events_from_cli_logs(res.split("\n"))
            serialized_events += [serialize_value(event) for event in events]

        return serialized_events

    return _execute_step_docker
