import os
from typing import List
from dagster.config.config_type import Array
from dagster.core.execution.plan.objects import StepFailureData


import docker
from dagster import check
from dagster.core.definitions.event_metadata import EventMetadataEntry
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster.core.executor.step_delegating.step_handler.base import StepHandler, StepHandlerContext
from dagster.serdes import serialize_dagster_namedtuple
from dagster.serdes.utils import hash_str
from dagster import Field, StringSource, check, executor
from dagster.core.definitions.executor import multiple_process_executor_requirements
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData, EventMetadataEntry
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.retries import get_retries_config
from dagster.core.executor.base import Executor
from dagster.core.executor.init import InitExecutorContext
from dagster.core.executor.step_delegating import StepDelegatingExecutor
from dagster.core.executor.step_delegating.step_handler import StepHandler
from dagster.core.executor.step_delegating.step_handler.base import StepHandlerContext
from dagster.core.types.dagster_type import Optional
from dagster.serdes.serdes import serialize_dagster_namedtuple
from dagster.utils import frozentags, merge_dicts
from dagster.utils.backcompat import experimental


@executor(
    name="docker",
    config_schema={
        "networks": Field(Array(str), is_required=False, default_value=[]),
        "env_vars": Field(Array(str), is_required=False, default_value=[]),
    },
    requirements=multiple_process_executor_requirements(),
)
@experimental
def docker_executor(init_context: InitExecutorContext) -> Executor:
    return StepDelegatingExecutor(
        DockerStepHandler(
            networks=init_context.executor_config["networks"],
            env_vars=init_context.executor_config["env_vars"],
        )
    )


class DockerStepHandler(StepHandler):
    def __init__(self, networks, env_vars):
        super().__init__()
        self._networks = check.opt_list_param(networks, "networks", of_type=str)
        self._env_vars = check.opt_list_param(env_vars, "env_vars", of_type=str)

    @property
    def name(self) -> str:
        return "DockerStepHandler"

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
            command=[
                "dagster",
                "api",
                "execute_step",
                serialize_dagster_namedtuple(execute_step_args),
            ],
            environment=(
                {env_name: os.getenv(env_name) for env_name in self._env_vars}
                if self._env_vars
                else {}
            ),
            labels={
                "created_by": "DagsterStepHandler",
                "step_key": execute_step_args.step_keys_to_execute[0],
                "run_id": execute_step_args.pipeline_run_id,
            },
        )

    def launch_step(self, step_handler_context: StepHandlerContext) -> List[DagsterEvent]:
        client = docker.client.from_env()

        step_image = (
            step_handler_context.execute_step_args.pipeline_origin.repository_origin.container_image
        )

        if not step_image:
            raise Exception("No image included to launch steps: " + str(step_image))

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
        print("checking docker health!")
        step_key = step_handler_context.execute_step_args.step_keys_to_execute[0]

        client = docker.client.from_env()

        container_name = self._get_container_name(
            step_handler_context.execute_step_args.pipeline_run_id,
            step_key,
        )

        try:
            container = client.containers.get(container_name)

        except Exception as e:  # pylint: disable=broad-except
            return [
                DagsterEvent(
                    event_type_value=DagsterEventType.STEP_FAILURE.value,
                    pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                    step_key=step_key,
                    message=f"Error when checking on container: {e}",
                    event_specific_data=StepFailureData(
                        error=None,
                        user_failure_data=None,
                    ),
                )
            ]
        else:
            if container.status != "running":
                return [
                    DagsterEvent(
                        event_type_value=DagsterEventType.STEP_FAILURE.value,
                        pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                        step_key=step_key,
                        message=f"Container {container_name} for step {step_key} is not running, status is {container.status}",
                        event_specific_data=StepFailureData(
                            error=None,
                            user_failure_data=None,
                        ),
                    )
                ]

        return []

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

        client = docker.client.from_env()

        try:
            container = client.containers.get(
                self._get_container_name(
                    step_handler_context.execute_step_args.pipeline_run_id,
                    step_handler_context.execute_step_args.step_keys_to_execute[0],
                )
            )
            container.stop()
        except Exception as e:  # pylint: disable=broad-except
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
