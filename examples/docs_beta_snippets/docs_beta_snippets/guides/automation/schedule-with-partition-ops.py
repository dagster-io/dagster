import dagster as dg


# Define the job
@dg.job(config=partitioned_config)  # noqa: F821
def partitioned_op_job(): ...


# highlight-start
# Create the schedule from the partition
partitioned_op_schedule = dg.build_schedule_from_partitioned_job(
    partitioned_op_job,
)
# highlight-end
