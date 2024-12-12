from typing import Callable, ContextManager

from dagster import job, op
from dagster._config import process_config, resolve_to_config_type
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context.system import PlanData, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import create_context_free_log_manager
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.init import InitExecutorContext
from dagster._core.executor.step_delegating.step_handler.base import StepHandlerContext
from dagster._core.instance import DagsterInstance
from dagster._core.storage.fs_io_manager import fs_io_manager
from dagster._core.test_utils import create_run_for_test
from dagster._grpc.types import ExecuteStepArgs

from dagster_aws.ecs.executor import _ECS_EXECUTOR_CONFIG_SCHEMA, ecs_executor


@job(
    executor_def=ecs_executor,
    resource_defs={"io_manager": fs_io_manager},
)
def bar():
    @op
    def foo():
        return 1

    foo()


def _get_executor(instance, job_def, executor_config=None):
    process_result = process_config(
        resolve_to_config_type(_ECS_EXECUTOR_CONFIG_SCHEMA), executor_config or {}
    )
    if not process_result.success:
        raise AssertionError(f"Process result errors: {process_result.errors}")

    return ecs_executor.executor_creation_fn(
        InitExecutorContext(
            job=job_def,
            executor_def=ecs_executor,
            executor_config=process_result.value,
            instance=instance,
        )
    )


def _step_handler_context(job_def, dagster_run, instance, executor):
    execution_plan = create_execution_plan(job_def)
    log_manager = create_context_free_log_manager(instance, dagster_run)

    plan_context = PlanOrchestrationContext(
        plan_data=PlanData(
            job=job_def,
            dagster_run=dagster_run,
            instance=instance,
            execution_plan=execution_plan,
            raise_on_error=True,
            retry_mode=RetryMode.DISABLED,
        ),
        log_manager=log_manager,
        executor=executor,
        output_capture=None,
    )

    execute_step_args = ExecuteStepArgs(
        reconstructable(bar).get_python_origin(),
        dagster_run.run_id,
        ["foo"],
        print_serialized_events=False,
    )

    return StepHandlerContext(
        instance=instance,
        plan_context=plan_context,
        steps=execution_plan.steps,
        execute_step_args=execute_step_args,
    )


def test_executor_init(instance_cm: Callable[..., ContextManager[DagsterInstance]]):
    with instance_cm() as instance:
        memory = 128
        cpu = 500
        env_var = {"key": "OVERRIDE_VAR", "value": "foo"}
        executor = _get_executor(
            instance,
            reconstructable(bar),
            {
                "cpu": cpu,
                "memory": memory,
                "task_overrides": {
                    "containerOverrides": [
                        {
                            "name": "run",
                            "environment": [env_var],
                        }
                    ],
                },
            },
        )
        run = create_run_for_test(
            instance,
            job_name="bar",
            job_code_origin=reconstructable(bar).get_python_origin(),
        )
        step_handler_context = _step_handler_context(
            job_def=reconstructable(bar),
            dagster_run=run,
            instance=instance,
            executor=executor,
        )
        run_task_kwargs = executor._step_handler._get_run_task_kwargs(  # noqa: SLF001
            run,
            ["my-command"],
            "asdasd",
            {},
            step_handler_context,
            executor._step_handler._get_container_context(step_handler_context),  # noqa: SLF001
        )
        overrides = run_task_kwargs["overrides"]

        assert overrides["cpu"] == str(cpu)
        assert overrides["memory"] == str(memory)

        run_container_overrides = overrides["containerOverrides"][0]

        assert run_container_overrides["name"] == "run"
        assert run_container_overrides["command"] == ["my-command"]

        assert env_var in run_container_overrides["environment"]


def test_executor_launch(instance_cm: Callable[..., ContextManager[DagsterInstance]]):
    with instance_cm() as instance:
        executor = _get_executor(instance, reconstructable(bar), {})
        run = create_run_for_test(
            instance,
            job_name="bar",
            job_code_origin=reconstructable(bar).get_python_origin(),
        )
        step_handler_context = _step_handler_context(
            job_def=reconstructable(bar),
            dagster_run=run,
            instance=instance,
            executor=executor,
        )
        from unittest.mock import MagicMock

        executor._step_handler.ecs.run_task = MagicMock(  # noqa: SLF001
            return_value={"tasks": [{"taskArn": "arn:123"}]}
        )

        executor._step_handler.launch_step(step_handler_context)  # noqa: SLF001

        run_task_kwargs = executor._step_handler.ecs.run_task.call_args[1]  # noqa: SLF001

        tags = run_task_kwargs["tags"]

        assert {
            "key": "dagster/run-id",
            "value": run.run_id,
        } in tags

        assert {
            "key": "dagster/job",
            "value": run.job_name,
        } in tags

        assert {
            "key": "dagster/step-key",
            "value": "foo",
        } in tags

        assert run_task_kwargs["overrides"]["containerOverrides"][0]["command"] == [
            "dagster",
            "api",
            "execute_step",
        ]

        found_executor_args_var = False
        for var in run_task_kwargs["overrides"]["containerOverrides"][0]["environment"]:
            if var["name"] == "DAGSTER_COMPRESSED_EXECUTE_STEP_ARGS":
                found_executor_args_var = True
                break

        assert found_executor_args_var
