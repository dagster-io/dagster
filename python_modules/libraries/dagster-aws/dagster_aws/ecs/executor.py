import json
import os
from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Optional, cast

import boto3
from dagster import (
    DagsterInvariantViolationError,
    DagsterRun,
    Field,
    IntSource,
    Permissive,
    _check as check,
    executor,
)
from dagster._core.definitions.executor_definition import multiple_process_executor_requirements
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.retries import RetryMode, get_retries_config
from dagster._core.execution.tags import get_tag_concurrency_limits_config
from dagster._core.executor.base import Executor
from dagster._core.executor.init import InitExecutorContext
from dagster._core.executor.step_delegating import (
    CheckStepHealthResult,
    StepDelegatingExecutor,
    StepHandler,
    StepHandlerContext,
)
from dagster._utils.backoff import backoff
from dagster._utils.merger import deep_merge_dicts

from dagster_aws.ecs.container_context import EcsContainerContext
from dagster_aws.ecs.launcher import STOPPED_STATUSES, EcsRunLauncher
from dagster_aws.ecs.tasks import (
    get_current_ecs_task,
    get_current_ecs_task_metadata,
    get_task_kwargs_from_current_task,
)
from dagster_aws.ecs.utils import RetryableEcsException, run_ecs_task, sanitize_tag

DEFAULT_STEP_TASK_RETRIES = "5"


_ECS_EXECUTOR_CONFIG_SCHEMA = {
    "run_task_kwargs": Field(
        Permissive({}),
        is_required=False,
        description=(
            "Additional arguments to which can be set to the boto3 run_task call. Will override values inherited from the ECS run launcher."
            " https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task"
            " for the available parameters."
        ),
    ),
    "cpu": Field(IntSource, is_required=False),
    "memory": Field(IntSource, is_required=False),
    "ephemeral_storage": Field(IntSource, is_required=False),
    "task_overrides": Field(
        Permissive({}),
        is_required=False,
    ),
    "retries": get_retries_config(),
    "max_concurrent": Field(
        IntSource,
        is_required=False,
        description=(
            "Limit on the number of tasks that will run concurrently within the scope "
            "of a Dagster run. Note that this limit is per run, not global."
        ),
    ),
    "tag_concurrency_limits": get_tag_concurrency_limits_config(),
}


@executor(
    name="ecs",
    config_schema=_ECS_EXECUTOR_CONFIG_SCHEMA,
    requirements=multiple_process_executor_requirements(),
)
def ecs_executor(init_context: InitExecutorContext) -> Executor:
    """Executor which launches steps as ECS tasks.

    To use the `ecs_executor`, set it as the `executor_def` when defining a job:

    .. literalinclude:: ../../../../../../python_modules/libraries/dagster-aws/dagster_aws_tests/ecs_tests/launcher_tests/executor_tests/test_example_executor_mode_def.py
        :start-after: start_marker
        :end-before: end_marker
        :language: python

    Then you can configure the executor with run config as follows:

    .. code-block:: YAML

        execution:
          config:
            cpu: 1024
            memory: 2048
            ephemeral_storage: 10
            task_overrides:
            containerOverrides:
              - name: run
                environment:
                  - name: MY_ENV_VAR
                    value: "my_value"

    `max_concurrent` limits the number of ECS tasks that will execute concurrently for one run. By default
    there is no limit- it will maximally parallel as allowed by the DAG. Note that this is not a
    global limit.

    Configuration set on the ECS tasks created by the `ECSRunLauncher` will also be
    set on the tasks created by the `ecs_executor`.

    Configuration set using `tags` on a `@job` will only apply to the `run` level. For configuration
    to apply at each `step` it must be set using `tags` for each `@op`.
    """
    run_launcher = init_context.instance.run_launcher

    check.invariant(
        isinstance(run_launcher, EcsRunLauncher),
        "Using the ecs_executor currently requires that the run be launched in an ECS task via the EcsRunLauncher.",
    )

    exc_cfg = init_context.executor_config

    return StepDelegatingExecutor(
        EcsStepHandler(
            run_launcher=run_launcher,  # type: ignore
            run_task_kwargs=exc_cfg.get("run_task_kwargs"),  # type: ignore
            cpu=exc_cfg.get("cpu"),  # type: ignore
            memory=exc_cfg.get("memory"),  # type: ignore
            ephemeral_storage=exc_cfg.get("ephemeral_storage"),  # type: ignore
            task_overrides=exc_cfg.get("task_overrides"),  # type:ignore
        ),
        retries=RetryMode.from_config(exc_cfg["retries"]),  # type: ignore
        max_concurrent=check.opt_int_elem(exc_cfg, "max_concurrent"),
        tag_concurrency_limits=check.opt_list_elem(exc_cfg, "tag_concurrency_limits"),
        should_verify_step=True,
    )


class EcsStepHandler(StepHandler):
    @property
    def name(self):
        return "EcsStepHandler"

    def __init__(
        self,
        run_launcher: EcsRunLauncher,
        run_task_kwargs: Optional[Mapping[str, Any]],
        cpu: Optional[int],
        memory: Optional[int],
        ephemeral_storage: Optional[int],
        task_overrides: Optional[Mapping[str, Any]],
    ):
        super().__init__()

        run_task_kwargs = run_task_kwargs or {}

        self.ecs = boto3.client("ecs")
        self.ec2 = boto3.resource("ec2")

        # confusingly, run_task expects cpu and memory value as strings
        self._cpu = str(cpu) if cpu else None
        self._memory = str(memory) if memory else None

        self._ephemeral_storage = ephemeral_storage
        self._task_overrides = check.opt_mapping_param(task_overrides, "task_overrides")

        current_task_metadata = get_current_ecs_task_metadata()
        current_task = get_current_ecs_task(
            self.ecs, current_task_metadata.task_arn, current_task_metadata.cluster
        )

        if run_launcher.use_current_ecs_task_config:
            current_task_kwargs = get_task_kwargs_from_current_task(
                self.ec2,
                current_task_metadata.cluster,
                current_task,
            )
        else:
            current_task_kwargs = {}

        run_launcher_kwargs = {**current_task_kwargs, **run_launcher.run_task_kwargs}

        self._cluster_arn = current_task["clusterArn"]
        self._task_definition_arn = current_task["taskDefinitionArn"]

        self._run_task_kwargs = {
            "taskDefinition": current_task["taskDefinitionArn"],
            **run_launcher_kwargs,
            **run_task_kwargs,
        }

        # TODO: change launch_step to return task ARN
        # this will be a breaking change so we need to wait for a minor release
        # to do this
        self._launched_tasks = {}

    def _get_run_task_kwargs(
        self,
        run: DagsterRun,
        args: Sequence[str],
        step_key: str,
        step_tags: Mapping[str, str],
        step_handler_context: StepHandlerContext,
        container_context: EcsContainerContext,
    ):
        run_launcher = check.inst(
            step_handler_context.instance.run_launcher,
            EcsRunLauncher,
            "ECS executor can only be enabled with the ECS run launcher",
        )

        run_task_kwargs = self._run_task_kwargs

        kwargs_from_tags = step_tags.get("ecs/run_task_kwargs")
        if kwargs_from_tags:
            run_task_kwargs = {**run_task_kwargs, **json.loads(kwargs_from_tags)}

        # convert tags to a dictionary for easy value overriding
        tags = {
            **{tag["key"]: tag["value"] for tag in run_task_kwargs.get("tags", [])},
            **{
                tag["key"]: tag["value"]
                for tag in run_launcher.build_ecs_tags_for_run_task(run, container_context)
            },
            **step_handler_context.dagster_run.dagster_execution_info,
            "dagster/step-key": sanitize_tag(step_key),
        }

        run_task_kwargs["tags"] = [
            {
                "key": key,
                "value": value,
            }
            for key, value in tags.items()
        ]

        task_overrides = self._get_task_overrides(step_tags) or {}

        task_overrides["containerOverrides"] = task_overrides.get("containerOverrides", [])

        # container name has to match since we are assuming we are using the same task
        executor_container_name = run_launcher.get_container_name(container_context)
        executor_env_vars = [
            {"name": env["name"], "value": env["value"]}
            for env in step_handler_context.execute_step_args.get_command_env()
        ]

        # inject Executor command and env vars into the container overrides
        # if they are defined
        # otherwise create a new container overrides for the executor container
        for container_overrides in task_overrides["containerOverrides"]:
            # try to update existing container overrides for the executor container
            if container_overrides["name"] == executor_container_name:
                if "command" in container_overrides and container_overrides["command"] != args:
                    raise DagsterInvariantViolationError(
                        f"The 'command' field for {executor_container_name} container is not allowed in the 'containerOverrides' field of the task overrides."
                    )

                # update environment variables & command
                container_overrides["command"] = args
                container_overrides["environment"] = (
                    container_overrides.get("environment", []) + executor_env_vars
                )
                break
        # if no existing container overrides for the executor container, add new container overrides
        else:
            task_overrides["containerOverrides"].append(
                {
                    "name": executor_container_name,
                    "command": args,
                    "environment": executor_env_vars,
                }
            )

        run_task_kwargs["overrides"] = deep_merge_dicts(
            run_task_kwargs.get("overrides", {}), task_overrides
        )

        return run_task_kwargs

    def _get_task_overrides(self, step_tags: Mapping[str, str]) -> dict[str, Any]:
        overrides = {**self._task_overrides}

        cpu = step_tags.get("ecs/cpu", self._cpu)
        memory = step_tags.get("ecs/memory", self._memory)

        if cpu:
            overrides["cpu"] = cpu
        if memory:
            overrides["memory"] = memory

        ephemeral_storage = step_tags.get("ecs/ephemeral_storage", self._ephemeral_storage)

        if ephemeral_storage:
            overrides["ephemeralStorage"] = {"sizeInGiB": int(ephemeral_storage)}

        if tag_overrides := step_tags.get("ecs/task_overrides"):
            overrides = deep_merge_dicts(overrides, json.loads(tag_overrides))

        return overrides

    def _get_step_id(self, step_handler_context: StepHandlerContext):
        """Step ID is used to identify the ECS task in the ECS cluster.
        It is unique to specific step being executed and takes into account op-level retries.
        It's used as a workaround to avoid having to return task ARN from launch_step.
        """
        step_key = self._get_step_key(step_handler_context)

        if step_handler_context.execute_step_args.known_state:
            retry_count = step_handler_context.execute_step_args.known_state.get_retry_state().get_attempt_count(
                step_key
            )
        else:
            retry_count = 0

        return "%s-%d" % (step_key, retry_count)  # noqa: UP031

    def _get_step_key(self, step_handler_context: StepHandlerContext) -> str:
        step_keys_to_execute = cast(
            list[str], step_handler_context.execute_step_args.step_keys_to_execute
        )
        assert len(step_keys_to_execute) == 1, "Launching multiple steps is not currently supported"
        return step_keys_to_execute[0]

    def _get_container_context(
        self, step_handler_context: StepHandlerContext
    ) -> EcsContainerContext:
        return EcsContainerContext.create_for_run(
            step_handler_context.dagster_run,
            cast(EcsRunLauncher, step_handler_context.instance.run_launcher),
        )

    def _run_task(self, **run_task_kwargs):
        return run_ecs_task(self.ecs, run_task_kwargs)

    def launch_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        step_key = self._get_step_key(step_handler_context)

        step_tags = step_handler_context.step_tags[step_key]

        container_context = self._get_container_context(step_handler_context)

        run = step_handler_context.dagster_run

        args = step_handler_context.execute_step_args.get_command_args(
            skip_serialized_namedtuple=True
        )

        run_task_kwargs = self._get_run_task_kwargs(
            run,
            args,
            step_key,
            step_tags,
            step_handler_context=step_handler_context,
            container_context=container_context,
        )

        task = backoff(
            self._run_task,
            retry_on=(RetryableEcsException,),
            kwargs=run_task_kwargs,
            max_retries=int(
                os.getenv("STEP_TASK_RETRIES", DEFAULT_STEP_TASK_RETRIES),
            ),
        )

        yield DagsterEvent.step_worker_starting(
            step_handler_context.get_step_context(step_key),
            message=f'Executing step "{step_key}" in ECS task.',
            metadata={
                "Task ARN": MetadataValue.text(task["taskArn"]),
            },
        )

        step_id = self._get_step_id(step_handler_context)

        self._launched_tasks[step_id] = task["taskArn"]

    def check_step_health(self, step_handler_context: StepHandlerContext) -> CheckStepHealthResult:
        step_key = self._get_step_key(step_handler_context)
        step_id = self._get_step_id(step_handler_context)

        try:
            task_arn = self._launched_tasks[step_id]
        except KeyError:
            return CheckStepHealthResult.unhealthy(
                reason=f"Task ARN for step {step_key} could not be found in executor's task map. This is likely a bug."
            )

        cluster_arn = self._cluster_arn

        tasks = self.ecs.describe_tasks(tasks=[task_arn], cluster=cluster_arn).get("tasks")

        if not tasks:
            return CheckStepHealthResult.unhealthy(
                reason=f"Task {task_arn} for step {step_key} could not be found."
            )

        t = tasks[0]
        if t.get("lastStatus") in STOPPED_STATUSES:
            failed_containers = []
            for c in t.get("containers"):
                if c.get("exitCode") != 0:
                    failed_containers.append(c)
            if len(failed_containers) > 0:
                cluster_failure_info = (
                    f"Task {t.get('taskArn')} failed.\n"
                    f"Stop code: {t.get('stopCode')}.\n"
                    f"Stop reason: {t.get('stoppedReason')}.\n"
                )
                for c in failed_containers:
                    exit_code = c.get("exitCode")
                    exit_code_msg = f" - exit code {exit_code}" if exit_code is not None else ""
                    cluster_failure_info += f"Container '{c.get('name')}' failed{exit_code_msg}.\n"

                return CheckStepHealthResult.unhealthy(reason=cluster_failure_info)

        return CheckStepHealthResult.healthy()

    def terminate_step(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        step_handler_context: StepHandlerContext,
    ) -> None:
        step_id = self._get_step_id(step_handler_context)
        step_key = self._get_step_key(step_handler_context)

        if step_id not in self._launched_tasks:
            # this can happen if an exception was raised during launch_step and the executor
            # is now trying to terminate all running steps
            return

        task_arn = self._launched_tasks[step_id]
        cluster_arn = self._cluster_arn

        DagsterEvent.engine_event(
            step_handler_context.get_step_context(step_key),
            message=f"Stopping task {task_arn} for step",
            event_specific_data=EngineEventData(),
        )

        self.ecs.stop_task(task=task_arn, cluster=cluster_arn)
