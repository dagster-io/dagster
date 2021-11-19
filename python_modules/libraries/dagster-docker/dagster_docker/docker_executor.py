import os
from typing import List

import docker
from dagster import check, executor
from dagster.core.definitions.executor_definition import multiple_process_executor_requirements
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData, EventMetadataEntry
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.retries import RetryMode, get_retries_config
from dagster.core.executor.base import Executor
from dagster.core.executor.init import InitExecutorContext
from dagster.core.executor.step_delegating import StepDelegatingExecutor
from dagster.core.executor.step_delegating.step_handler.base import StepHandler, StepHandlerContext
from dagster.serdes.utils import hash_str
from dagster.utils import merge_dicts
from dagster.utils.backcompat import experimental
from dagster_docker.utils import DOCKER_CONFIG_SCHEMA, validate_docker_config, validate_docker_image


@executor(
    name="docker",
    config_schema=merge_dicts(
        DOCKER_CONFIG_SCHEMA,
        {
            "retries": get_retries_config(),
        },
    ),
    requirements=multiple_process_executor_requirements(),
)
@experimental
def docker_executor(init_context: InitExecutorContext) -> Executor:
    from . import DockerRunLauncher

    image = init_context.executor_config.get("image")
    registry = init_context.executor_config.get("registry")
    env_vars = init_context.executor_config.get("env_vars")
    network = init_context.executor_config.get("network")
    networks = init_context.executor_config.get("networks")
    container_kwargs = init_context.executor_config.get("container_kwargs")

    run_launcher = init_context.instance.run_launcher
    if isinstance(run_launcher, DockerRunLauncher):
        image = image or run_launcher.image
        registry = registry or run_launcher.registry
        env_vars = run_launcher.env_vars + (env_vars or [])
        networks = run_launcher.networks + (networks or [])
        container_kwargs = merge_dicts(run_launcher.container_kwargs, container_kwargs or {})

    validate_docker_config(network, networks, container_kwargs)

    return StepDelegatingExecutor(
        DockerStepHandler(
            image,
            registry,
            env_vars,
            network,
            networks,
            container_kwargs,
        ),
        retries=RetryMode.from_config(init_context.executor_config["retries"]),
    )


class DockerStepHandler(StepHandler):
    def __init__(
        self,
        image=None,
        registry=None,
        env_vars=None,
        network=None,
        networks=None,
        container_kwargs=None,
    ):
        super().__init__()

        self._image = image
        self._registry = registry
        self._env_vars = env_vars

        if network:
            self._networks = [network]
        elif networks:
            self._networks = networks
        else:
            self._networks = []

        self._container_kwargs = check.opt_dict_param(
            container_kwargs, "container_kwargs", key_type=str
        )

    @property
    def name(self) -> str:
        return "DockerStepHandler"

    def _get_client(self):
        client = docker.client.from_env()
        if self._registry:
            client.login(
                registry=self._registry["url"],
                username=self._registry["username"],
                password=self._registry["password"],
            )
        return client

    def _get_container_name(self, run_id, step_key):
        return f"dagster-job-{hash_str(run_id + step_key)}"

    def _create_step_container(self, client, step_image, execute_step_args):
        return client.containers.create(
            step_image,
            name=self._get_container_name(
                execute_step_args.pipeline_run_id, execute_step_args.step_keys_to_execute[0]
            ),
            detach=True,
            network=self._networks[0] if len(self._networks) else None,
            command=execute_step_args.get_command_args(),
            environment=(
                {env_name: os.getenv(env_name) for env_name in self._env_vars}
                if self._env_vars
                else {}
            ),
            **self._container_kwargs,
        )

    def launch_step(self, step_handler_context: StepHandlerContext) -> List[DagsterEvent]:
        client = self._get_client()

        step_image = (
            step_handler_context.execute_step_args.pipeline_origin.repository_origin.container_image
        )

        if not step_image:
            step_image = self._image

        if not step_image:
            raise Exception("No docker image specified by the executor config or repository")

        validate_docker_image(step_image)

        try:
            step_container = self._create_step_container(
                client, step_image, step_handler_context.execute_step_args
            )
        except docker.errors.ImageNotFound:
            client.images.pull(step_image)
            step_container = self._create_step_container(
                client, step_image, step_handler_context.execute_step_args
            )

        if len(self._networks) > 1:
            for network_name in self._networks[1:]:
                network = client.networks.get(network_name)
                network.connect(step_container)

        assert (
            len(step_handler_context.execute_step_args.step_keys_to_execute) == 1
        ), "Launching multiple steps is not currently supported"
        step_key = step_handler_context.execute_step_args.step_keys_to_execute[0]

        events = [
            DagsterEvent(
                event_type_value=DagsterEventType.ENGINE_EVENT.value,
                pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                step_key=step_key,
                message="Launching step in Docker container",
                event_specific_data=EngineEventData(
                    [
                        EventMetadataEntry.text(step_key, "Step key"),
                        EventMetadataEntry.text(step_container.id, "Docker container id"),
                    ],
                ),
            )
        ]

        step_container.start()

        return events

    def check_step_health(self, step_handler_context: StepHandlerContext) -> List[DagsterEvent]:
        step_key = step_handler_context.execute_step_args.step_keys_to_execute[0]

        client = self._get_client()

        container_name = self._get_container_name(
            step_handler_context.execute_step_args.pipeline_run_id,
            step_key,
        )

        try:
            container = client.containers.get(container_name)

        except Exception as e:
            return [
                DagsterEvent(
                    event_type_value=DagsterEventType.STEP_FAILURE.value,
                    pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                    step_key=step_key,
                    message=f"Error when checking on step container health: {e}",
                    event_specific_data=StepFailureData(
                        error=None,
                        user_failure_data=None,
                    ),
                )
            ]

        if container.status == "running":
            return []

        try:
            container_info = container.wait(timeout=0.1)
        except Exception as e:
            return [
                DagsterEvent(
                    event_type_value=DagsterEventType.STEP_FAILURE.value,
                    pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                    step_key=step_key,
                    message=f"Container status is {container.status}. Hit exception attempting to get its return code: {e}",
                    event_specific_data=StepFailureData(
                        error=None,
                        user_failure_data=None,
                    ),
                )
            ]

        ret_code = container_info.get("StatusCode")
        if ret_code == 0:
            return []

        return [
            DagsterEvent(
                event_type_value=DagsterEventType.STEP_FAILURE.value,
                pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                step_key=step_key,
                message=f"Container status is {container.status}. Return code is {str(ret_code)}.",
                event_specific_data=StepFailureData(
                    error=None,
                    user_failure_data=None,
                ),
            )
        ]

    def terminate_step(self, step_handler_context: StepHandlerContext) -> List[DagsterEvent]:

        assert (
            len(step_handler_context.execute_step_args.step_keys_to_execute) == 1
        ), "Launching multiple steps is not currently supported"
        step_key = step_handler_context.execute_step_args.step_keys_to_execute[0]

        events = [
            DagsterEvent(
                event_type_value=DagsterEventType.ENGINE_EVENT.value,
                pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                step_key=step_key,
                message="Stopping Docker container for step",
                event_specific_data=EngineEventData(),
            )
        ]

        client = self._get_client()

        try:
            container = client.containers.get(
                self._get_container_name(
                    step_handler_context.execute_step_args.pipeline_run_id,
                    step_handler_context.execute_step_args.step_keys_to_execute[0],
                )
            )
            container.stop()
        except Exception as e:
            events.append(
                DagsterEvent(
                    event_type_value=DagsterEventType.ENGINE_EVENT.value,
                    pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                    step_key=step_key,
                    message=f"Hit error while terminating Docker container:\n{e}",
                    event_specific_data=EngineEventData(),
                )
            )

        return events
