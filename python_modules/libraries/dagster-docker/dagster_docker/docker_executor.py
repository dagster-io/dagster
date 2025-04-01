from collections.abc import Iterator
from typing import Optional, cast

import dagster._check as check
import docker
import docker.errors
from dagster import Field, IntSource, executor
from dagster._annotations import beta
from dagster._core.definitions.executor_definition import multiple_process_executor_requirements
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.retries import RetryMode, get_retries_config
from dagster._core.execution.tags import get_tag_concurrency_limits_config
from dagster._core.executor.base import Executor
from dagster._core.executor.init import InitExecutorContext
from dagster._core.executor.step_delegating import StepDelegatingExecutor
from dagster._core.executor.step_delegating.step_handler.base import (
    CheckStepHealthResult,
    StepHandler,
    StepHandlerContext,
)
from dagster._core.origin import JobPythonOrigin
from dagster._core.utils import parse_env_var
from dagster._utils.merger import merge_dicts
from dagster_shared.serdes.utils import hash_str

from dagster_docker.container_context import DockerContainerContext
from dagster_docker.utils import DOCKER_CONFIG_SCHEMA, validate_docker_config, validate_docker_image


@executor(
    name="docker",
    config_schema=merge_dicts(
        DOCKER_CONFIG_SCHEMA,
        {
            "retries": get_retries_config(),
            "max_concurrent": Field(
                IntSource,
                is_required=False,
                description=(
                    "Limit on the number of containers that will run concurrently within the scope "
                    "of a Dagster run. Note that this limit is per run, not global."
                ),
            ),
            "tag_concurrency_limits": get_tag_concurrency_limits_config(),
        },
    ),
    requirements=multiple_process_executor_requirements(),
)
@beta
def docker_executor(init_context: InitExecutorContext) -> Executor:
    """Executor which launches steps as Docker containers.

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
    max_concurrent = check.opt_int_elem(config, "max_concurrent")
    tag_concurrency_limits = check.opt_list_elem(config, "tag_concurrency_limits")

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
        max_concurrent=max_concurrent,
        tag_concurrency_limits=tag_concurrency_limits,
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
        from dagster_docker import DockerRunLauncher

        image = cast(
            JobPythonOrigin, step_handler_context.dagster_run.job_code_origin
        ).repository_origin.container_image
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
        # for the whole StepHandler but we need access to the DagsterRun for that

        from dagster_docker.docker_run_launcher import DockerRunLauncher

        run_launcher = step_handler_context.instance.run_launcher
        run_target = DockerContainerContext.create_for_run(
            step_handler_context.dagster_run,
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

    def _get_step_key(self, step_handler_context: StepHandlerContext) -> str:
        step_keys_to_execute = cast(
            list[str], step_handler_context.execute_step_args.step_keys_to_execute
        )
        assert len(step_keys_to_execute) == 1, "Launching multiple steps is not currently supported"
        return step_keys_to_execute[0]

    def _get_container_name(self, step_handler_context: StepHandlerContext):
        execute_step_args = step_handler_context.execute_step_args
        run_id = execute_step_args.run_id
        step_key = self._get_step_key(step_handler_context)

        step_name = f"dagster-step-{hash_str(run_id + step_key)}"

        if execute_step_args.known_state:
            retry_state = execute_step_args.known_state.get_retry_state()
            retry_number = retry_state.get_attempt_count(step_key)
            if retry_number:
                step_name = f"{step_name}-{retry_number}"

        return step_name

    def _create_step_container(
        self,
        client,
        container_context,
        step_image,
        step_handler_context: StepHandlerContext,
    ):
        execute_step_args = step_handler_context.execute_step_args
        step_keys_to_execute = check.not_none(execute_step_args.step_keys_to_execute)
        assert len(step_keys_to_execute) == 1, "Launching multiple steps is not currently supported"
        step_key = step_keys_to_execute[0]

        container_kwargs = {**container_context.container_kwargs}
        if "stop_timeout" in container_kwargs:
            # This should work, but does not due to https://github.com/docker/docker-py/issues/3168
            # Pull it out and apply it in the terminate() method instead
            del container_kwargs["stop_timeout"]

        env_vars = dict([parse_env_var(env_var) for env_var in container_context.env_vars])
        env_vars["DAGSTER_RUN_JOB_NAME"] = step_handler_context.dagster_run.job_name
        env_vars["DAGSTER_RUN_STEP_KEY"] = step_key
        return client.containers.create(
            step_image,
            name=self._get_container_name(step_handler_context),
            detach=True,
            network=container_context.networks[0] if len(container_context.networks) else None,
            command=execute_step_args.get_command_args(),
            environment=env_vars,
            **container_kwargs,
        )

    def launch_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        container_context = self._get_docker_container_context(step_handler_context)

        client = self._get_client(container_context)

        step_image = self._get_image(step_handler_context)
        validate_docker_image(step_image)

        try:
            step_container = self._create_step_container(
                client, container_context, step_image, step_handler_context
            )
        except docker.errors.ImageNotFound:
            client.images.pull(step_image)
            step_container = self._create_step_container(
                client, container_context, step_image, step_handler_context
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

        yield DagsterEvent.step_worker_starting(
            step_handler_context.get_step_context(step_key),
            message="Launching step in Docker container.",
            metadata={
                "Docker container id": step_container.id,
            },
        )
        step_container.start()

    def check_step_health(self, step_handler_context: StepHandlerContext) -> CheckStepHealthResult:
        container_context = self._get_docker_container_context(step_handler_context)

        client = self._get_client(container_context)

        container_name = self._get_container_name(step_handler_context)
        step_key = self._get_step_key(step_handler_context)

        try:
            container = client.containers.get(container_name)
        except docker.errors.NotFound:
            return CheckStepHealthResult.unhealthy(
                reason=f"Docker container {container_name} for step {step_key} could not be found."
            )

        if container.status == "running":
            return CheckStepHealthResult.healthy()

        try:
            container_info = container.wait(timeout=0.1)
        except Exception as e:
            raise Exception(
                f"Container status is {container.status}. Raised exception attempting to get its"
                " return code."
            ) from e

        ret_code = container_info.get("StatusCode")
        if ret_code == 0:
            return CheckStepHealthResult.healthy()

        return CheckStepHealthResult.unhealthy(
            reason=f"Container status is {container.status}. Return code is {ret_code}."
        )

    def terminate_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        container_context = self._get_docker_container_context(step_handler_context)

        step_keys_to_execute = check.not_none(
            step_handler_context.execute_step_args.step_keys_to_execute
        )
        assert (
            len(step_keys_to_execute) == 1
        ), "Terminating multiple steps is not currently supported"
        step_key = step_keys_to_execute[0]

        container_name = self._get_container_name(step_handler_context)

        yield DagsterEvent.engine_event(
            step_handler_context.get_step_context(step_key),
            message=f"Stopping Docker container {container_name} for step.",
            event_specific_data=EngineEventData(),
        )

        client = self._get_client(container_context)

        container = client.containers.get(container_name)

        stop_timeout = container_context.container_kwargs.get("stop_timeout")

        container.stop(timeout=stop_timeout)
