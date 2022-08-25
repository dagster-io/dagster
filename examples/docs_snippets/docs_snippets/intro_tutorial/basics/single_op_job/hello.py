# isort: skip_file

# start_op_marker
import os
from dagster import job, op, get_dagster_logger


@op
def get_file_sizes():
    files = [f for f in os.listdir(".") if os.path.isfile(f)]
    for f in files:
        get_dagster_logger().info(f"Size of {f} is {os.path.getsize(f)}")


# end_op_marker


# start_job_marker
@job
def file_sizes_job():
    get_file_sizes()


# end_job_marker

# start_execute_marker
if __name__ == "__main__":
    result = file_sizes_job.execute_in_process()

# end_execute_marker
