from dagster import DagsterInstance, execute_pipeline, reexecute_pipeline
from docs_snippets.guides.dagster.reexecution.unreliable_job import unreliable_job

instance = DagsterInstance.ephemeral()

# Initial execution
job_execution_result = execute_pipeline(unreliable_job, instance=instance)

if not job_execution_result.success:
    # re-execute the entire job
    reexecute_pipeline(
        unreliable_job,
        parent_run_id=job_execution_result.run_id,
        instance=instance,
    )


# end_initial_execution_marker

# start_partial_execution_marker

# re-execute the job, but only the "unreliable" op and all its descendents
reexecute_pipeline(
    unreliable_job,
    parent_run_id=job_execution_result.run_id,
    instance=instance,
    step_selection=["unreliable*"],
)

# end_partial_execution_marker
