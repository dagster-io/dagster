from dagster import pipeline
from dagster.core.definitions.reconstructable import reconstructable
from dagster.core.executor.step_delegating import StepHandlerContext
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.grpc.types import ExecuteStepArgs


@pipeline
def foo_pipline():
    pass


def test_step_handler_context():
    recon_pipeline = reconstructable(foo_pipline)
    with instance_for_test() as instance:
        run = create_run_for_test(instance)

        args = ExecuteStepArgs(
            pipeline_origin=recon_pipeline.get_python_origin(),
            pipeline_run_id=run.run_id,
            step_keys_to_execute=run.step_keys_to_execute,
            instance_ref=None,
        )
        ctx = StepHandlerContext(
            instance=instance,
            execute_step_args=args,
            pipeline_run=run,
        )

        reloaded_ctx = StepHandlerContext.deserialize(instance, ctx.serialize())
        assert reloaded_ctx.execute_step_args == args
        assert reloaded_ctx.pipeline_run == run
