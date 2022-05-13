from typing import List, Optional

import docker
from dagster_docker.utils import DOCKER_CONFIG_SCHEMA, validate_docker_config, validate_docker_image

import dagster._check as check
from dagster import executor
from dagster.core.definitions.executor_definition import multiple_process_executor_requirements
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData, MetadataEntry
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.retries import RetryMode, get_retries_config
from dagster.core.executor.base import Executor
from dagster.core.executor.init import InitExecutorContext
from dagster.core.executor.step_delegating import StepDelegatingExecutor
from dagster.core.executor.step_delegating.step_handler.base import StepHandler, StepHandlerContext
from dagster.serdes.utils import hash_str
from dagster.utils import merge_dicts
from dagster.utils.backcompat import experimental

from .container_context import DockerContainerContext
from .utils import parse_env_var


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
    """
    Executor which launches steps as Docker containers.

    To use the `docker_executor`, set it as the `executor_def` when defining a job:

    .. literalinclude:: ../../../../../../python_modules/libraries/dagster-docker/dagster_docker_tests/test_example_executor.py
       :start-after: start_marker
       :end-before: end_marker
       :language: python

    Then you can configure the executor with run config as follows:

    .. code-block:: YAML

        execution:
          config:
            registry: ...
            network: ...
            networks: ...
            container_kwargs: ...

    If you're using the DockerRunLauncher, configuration set on the containers created by the run
    launcher will also be set on the containers that are created for each step.
    """

    config = init_context.executor_config
    image = check.opt_str_elem(config, "image")
    registry = check.opt_dict_elem(config, "registry", key_type=str)
    env_vars = check.opt_list_elem(config, "env_vars", of_type=str)
    network = check.opt_str_elem(config, "network")
    networks = check.opt_list_elem(config, "networks", of_type=str)
    container_kwargs = check.opt_dict_elem(config, "container_kwargs", key_type=str)
    retries = check.dict_elem(config, "retries", key_type=str)

    validate_docker_config(network, networks, container_kwargs)

    if network and not networks:
        networks = [network]

    container_context = DockerContainerContext(
        registry=registry,
        env_vars=env_vars or [],
        networks=networks or [],
        container_kwargs=container_kwargs,
    )

    return StepDelegatingExecutor(
        DockerStepHandler(image, container_context),
        retries=check.not_none(RetryMode.from_config(retries)),
    )


class DockerStepHandler(StepHandler):
    def __init__(
        self,
        image: Optional[str],
        container_context: DockerContainerContext,
    ):
        super().__init__()

        self._image = check.opt_str_param(image, "image")
        self._container_context = check.inst_param(
            container_context, "container_context", DockerContainerContext
        )

    def _get_image(self, step_handler_context: StepHandlerContext):
        from . import DockerRunLauncher

        image = (
            step_handler_context.execute_step_args.pipeline_origin.repository_origin.container_image
        )
        if not image:
            image = self._image

        run_launcher = step_handler_context.instance.run_launcher

        if not image and isinstance(run_launcher, DockerRunLauncher):
            image = run_launcher.image

        if not image:
            raise Exception("No docker image specified by the executor config or repository")

        return image

    def _get_docker_container_context(self, step_handler_context: StepHandlerContext):
        # This doesn't vary per step: would be good to have a hook where it can be set once
        # for the whole StepHandler but we need access to the PipelineRun for that

        from .docker_run_launcher import DockerRunLauncher

        run_launcher = step_handler_context.instance.run_launcher
        run_target = DockerContainerContext.create_for_run(
            step_handler_context.pipeline_run,
            run_launcher if isinstance(run_launcher, DockerRunLauncher) else None,
        )

        merged_container_context = run_target.merge(self._container_context)

        validate_docker_config(
            network=None,
            networks=merged_container_context.networks,
            container_kwargs=merged_container_context.container_kwargs,
        )

        return merged_container_context

    @property
    def name(self) -> str:
        return "DockerStepHandler"

    def _get_client(self, docker_container_context: DockerContainerContext):
        client = docker.client.from_env()
        if docker_container_context.registry:
            client.login(
                registry=docker_container_context.registry["url"],
                username=docker_container_context.registry["username"],
                password=docker_container_context.registry["password"],
            )
        return client

    def _get_container_name(self, run_id, step_key):
        return f"dagster-step-{hash_str(run_id + step_key)}"

    def _create_step_container(self, client, container_context, step_image, execute_step_args):
        return client.containers.create(
            step_image,
            name=self._get_container_name(
                execute_step_args.pipeline_run_id, execute_step_args.step_keys_to_execute[0]
            ),
            detach=True,
            network=container_context.networks[0] if len(container_context.networks) else None,
            command=execute_step_args.get_command_args(),
            environment=(dict([parse_env_var(env_var) for env_var in container_context.env_vars])),
            **container_context.container_kwargs,
        )

    def launch_step(self, step_handler_context: StepHandlerContext) -> List[DagsterEvent]:
        container_context = self._get_docker_container_context(step_handler_context)

        client = self._get_client(container_context)

        step_image = self._get_image(step_handler_context)
        validate_docker_image(step_image)

        try:
            step_container = self._create_step_container(
                client, container_context, step_image, step_handler_context.execute_step_args
            )
        except docker.errors.ImageNotFound:
            client.images.pull(step_image)
            step_container = self._create_step_container(
                client, container_context, step_image, step_handler_context.execute_step_args
            )

        if len(container_context.networks) > 1:
            for network_name in container_context.networks[1:]:
                network = client.networks.get(network_name)
                network.connect(step_container)

        step_keys_to_execute = check.not_none(
            step_handler_context.execute_step_args.step_keys_to_execute
        )
        assert len(step_keys_to_execute) == 1, "Launching multiple steps is not currently supported"
        step_key = step_keys_to_execute[0]

        events = [
            DagsterEvent(
                event_type_value=DagsterEventType.ENGINE_EVENT.value,
                pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                step_key=step_key,
                message="Launching step in Docker container",
                event_specific_data=EngineEventData(
                    [
                        MetadataEntry("Step key", value=step_key),
                        MetadataEntry("Docker container id", value=step_container.id),
                    ],
                ),
            )
        ]

        step_container.start()

        return events

    def check_step_health(self, step_handler_context: StepHandlerContext) -> List[DagsterEvent]:
        step_keys_to_execute = check.not_none(
            step_handler_context.execute_step_args.step_keys_to_execute
        )
        step_key = step_keys_to_execute[0]
        container_context = self._get_docker_container_context(step_handler_context)

        client = self._get_client(container_context)

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
        container_context = self._get_docker_container_context(step_handler_context)

        step_keys_to_execute = check.not_none(
            step_handler_context.execute_step_args.step_keys_to_execute
        )
        assert len(step_keys_to_execute) == 1, "Launching multiple steps is not currently supported"
        step_key = step_keys_to_execute[0]

        events = [
            DagsterEvent(
                event_type_value=DagsterEventType.ENGINE_EVENT.value,
                pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                step_key=step_key,
                message="Stopping Docker container for step",
                event_specific_data=EngineEventData(),
            )
        ]

        client = self._get_client(container_context)

        try:
            container = client.containers.get(
                self._get_container_name(
                    step_handler_context.execute_step_args.pipeline_run_id,
                    step_keys_to_execute[0],
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
