from dagster import DagsterInstance

# Sequential execution - always single-threaded
result = my_job.execute_in_process()
# Fast for small tasks, but no parallelism