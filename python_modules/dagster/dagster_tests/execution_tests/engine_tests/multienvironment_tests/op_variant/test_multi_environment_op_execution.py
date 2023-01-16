import tempfile

from dagster import job, op
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import execute_job
from dagster._core.execution.context.system import IStepContext
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.multi_environment.multi_environment_step_handler import (
    MultiEnvironmentStepHandler,
    RemoteEnvironmentSingleStepHandler,
)
from dagster._core.executor.step_delegating.step_delegating_executor import StepDelegatingExecutor
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path

from dagster_tests.execution_tests.engine_tests.multienvironment_tests.python_script_single_step_handler import (
    PythonScriptSingleStepHandler,
)


@op
def returns_one() -> int:
    raise NotImplementedError("not executed, metadata only")


@op
def returns_two() -> int:
    raise NotImplementedError("not executed, metadata only")


@op
def add(x: int, y: int) -> int:
    raise NotImplementedError("not executed, metadata only")


def _get_remote_step_handler(step_context: IStepContext) -> RemoteEnvironmentSingleStepHandler:
    scripts = {
        "returns_one": file_relative_path(__file__, "returns_one.py"),
        "returns_two": file_relative_path(__file__, "returns_two.py"),
        "add": file_relative_path(__file__, "add.py"),
    }
    return PythonScriptSingleStepHandler(scripts[step_context.step.key])


@job(
    executor_def=ExecutorDefinition.hardcoded_executor(
        StepDelegatingExecutor(
            step_handler=MultiEnvironmentStepHandler(_get_remote_step_handler),
            retries=RetryMode.DISABLED,
            check_step_health_interval_seconds=1,
        )
    )
)
def a_job():
    add(returns_one(), returns_two())


def test_multi_environment_with_intermediates():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        with instance_for_test(temp_dir=tmpdir_path) as instance:
            with execute_job(job=reconstructable(a_job), instance=instance) as result:
                assert result.success
                assert result.output_for_node("returns_one") == 1
                assert result.output_for_node("returns_two") == 2
                assert result.output_for_node("add") == 3
