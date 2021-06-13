from dagster import DagsterInstance, execute_pipeline, reexecute_pipeline
from reexecution.pipeline.unreliable_pipeline import unreliable_pipeline


def reexecution_api_example():
    instance = DagsterInstance.ephemeral()
    run_config = {"intermediate_storage": {"filesystem": {}}}

    # Initial execution
    pipeline_result_full = execute_pipeline(unreliable_pipeline, run_config=run_config, instance=instance)

    if not pipeline_result_full.success:
        # Re-execution: Entire pipeline
        reexecution_result_full = reexecute_pipeline(
            unreliable_pipeline,
            parent_run_id=pipeline_result_full.run_id,
            run_config=run_config,
            instance=instance,
        )
