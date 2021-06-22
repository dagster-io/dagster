from dagster import DagsterInstance, execute_pipeline, reexecute_pipeline
from reexecution.unreliable_pipeline import unreliable_pipeline


def reexecution():
    instance = DagsterInstance.ephemeral()

    # Initial execution
    pipeline_result_full = execute_pipeline(unreliable_pipeline, instance=instance)

    if not pipeline_result_full.success:
        # Re-execution: Entire pipeline
        reexecution_result_full = reexecute_pipeline(
            unreliable_pipeline,
            parent_run_id=pipeline_result_full.run_id,
            instance=instance,
        )


# end_initial_execution_marker

instance = DagsterInstance.ephemeral()
pipeline_result_full = execute_pipeline(unreliable_pipeline, instance=instance)

# start_partial_execution_marker

# Re-execution: Starting with the "unreliable" solid and all its descendents
reexecution_result_specific_selection = reexecute_pipeline(
    unreliable_pipeline,
    parent_run_id=pipeline_result_full.run_id,
    instance=instance,
    solid_selection=["unreliable+*"],
)

# end_partial_execution_marker
