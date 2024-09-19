from dagster import job
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context.system import PlanData, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import create_context_free_log_manager
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.init import InitExecutorContext
from dagster._core.executor.step_delegating import StepHandlerContext
from dagster._core.test_utils import create_run_for_test, instance_for_test
from dagster._grpc.types import ExecuteStepArgs

from dagster_tests.execution_tests.engine_tests.test_step_delegating_executor import (
    test_step_delegating_executor,
)


@job
def foo_pipline():
    pass


def _get_executor(instance, pipeline, executor_config=None):
    return test_step_delegating_executor.executor_creation_fn(
        InitExecutorContext(
            job=pipeline,
            executor_def=test_step_delegating_executor,
            executor_config=executor_config or {"retries": {}},
            instance=instance,
        )
    )


def test_step_handler_context():
    recon_job = reconstructable(foo_pipline)
    with instance_for_test() as instance:
        run = create_run_for_test(instance, job_code_origin=recon_job.get_python_origin())

        execution_plan = create_execution_plan(recon_job)
        log_manager = create_context_free_log_manager(instance, run)

        executor = _get_executor(instance, recon_job)

        plan_context = PlanOrchestrationContext(
            plan_data=PlanData(
                job=recon_job,
                dagster_run=run,
                instance=instance,
                execution_plan=execution_plan,
                raise_on_error=True,
                retry_mode=RetryMode.DISABLED,
            ),
            log_manager=log_manager,
            executor=executor,
            output_capture=None,
        )

        args = ExecuteStepArgs(
            job_origin=recon_job.get_python_origin(),
            run_id=run.run_id,
            step_keys_to_execute=run.step_keys_to_execute,
            instance_ref=None,
            print_serialized_events=False,
        )
        ctx = StepHandlerContext(
            instance=instance,
            plan_context=plan_context,
            steps=execution_plan.steps,
            execute_step_args=args,
            dagster_run=run,
        )

        assert ctx.execute_step_args == args
        assert ctx.dagster_run == run
