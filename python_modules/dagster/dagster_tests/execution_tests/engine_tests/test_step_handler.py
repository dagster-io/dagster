from dagster import pipeline
from dagster.core.definitions.reconstruct import reconstructable
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context.system import PlanData, PlanOrchestrationContext
from dagster.core.execution.context_creation_pipeline import create_context_free_log_manager
from dagster.core.execution.retries import RetryMode
from dagster.core.executor.init import InitExecutorContext
from dagster.core.executor.step_delegating import StepHandlerContext
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.grpc.types import ExecuteStepArgs

from .test_step_delegating_executor import test_step_delegating_executor


@pipeline
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
    recon_pipeline = reconstructable(foo_pipline)
    with instance_for_test() as instance:
        run = create_run_for_test(instance, pipeline_code_origin=recon_pipeline.get_python_origin())

        execution_plan = create_execution_plan(recon_pipeline)
        log_manager = create_context_free_log_manager(instance, run)

        executor = _get_executor(instance, recon_pipeline)

        plan_context = PlanOrchestrationContext(
            plan_data=PlanData(
                pipeline=recon_pipeline,
                pipeline_run=run,
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
            pipeline_origin=recon_pipeline.get_python_origin(),
            pipeline_run_id=run.run_id,
            step_keys_to_execute=run.step_keys_to_execute,
            instance_ref=None,
        )
        ctx = StepHandlerContext(
            instance=instance,
            plan_context=plan_context,
            steps=execution_plan.steps,
            execute_step_args=args,
            pipeline_run=run,
        )

        assert ctx.execute_step_args == args
        assert ctx.pipeline_run == run
