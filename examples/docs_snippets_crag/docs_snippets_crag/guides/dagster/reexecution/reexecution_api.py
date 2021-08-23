from dagster import DagsterInstance, execute_pipeline, reexecute_pipeline
from docs_snippets_crag.guides.dagster.reexecution.unreliable_pipeline import unreliable_pipeline

instance = DagsterInstance.ephemeral()
# Initial execution
pipeline_result_full = execute_pipeline(unreliable_pipeline, instance=DagsterInstance.ephemeral())

if not pipeline_result_full.success:
    # Re-execution: Entire pipeline
    reexecute_pipeline(
        unreliable_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        instance=instance,
    )


# end_initial_execution_marker

# start_partial_execution_marker

# Re-execution: Starting with the "unreliable" solid and all its descendents
reexecution_result_specific_selection = reexecute_pipeline(
    unreliable_pipeline,
    parent_run_id=pipeline_result_full.run_id,
    instance=instance,
    step_selection=["unreliable+*"],
)

# end_partial_execution_marker
