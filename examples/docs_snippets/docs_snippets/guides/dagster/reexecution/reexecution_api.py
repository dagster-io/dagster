# isort: split
from_failure_result = None
result = None
# start_initial_execution_marker
from dagster import DagsterInstance, ReexecutionOptions, execute_job, reconstructable
from docs_snippets.guides.dagster.reexecution.unreliable_job import unreliable_job

instance = DagsterInstance.ephemeral()

# Initial execution
initial_result = execute_job(reconstructable(unreliable_job), instance=instance)

if not initial_result.success:
    options = ReexecutionOptions.from_failure(initial_result.run_id, instance)
    # re-execute the entire job
    from_failure_result = execute_job(
        reconstructable(unreliable_job), instance=instance, reexecution_options=options
    )


# end_initial_execution_marker
# isort: split

# start_partial_execution_marker

# re-execute the job, but only the "unreliable" op and all its descendents
options = ReexecutionOptions(
    parent_run_id=initial_result.run_id, step_selection=["unreliable*"]
)
result = execute_job(
    reconstructable(unreliable_job),
    instance=instance,
    reexecution_options=options,
)

# end_partial_execution_marker
