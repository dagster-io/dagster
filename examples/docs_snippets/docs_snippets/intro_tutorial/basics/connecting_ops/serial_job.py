import os

from dagster import get_dagster_logger, job, op


@op
def get_file_sizes():
    files = [f for f in os.listdir(".") if os.path.isfile(f)]
    return {f: os.path.getsize(f) for f in files}


@op
def report_total_size(file_sizes):
    total_size = sum(file_sizes.values())
    # In real life, we'd send an email or Slack message instead of just logging:
    get_dagster_logger().info(f"Total size: {total_size}")


@job
def serial():
    report_total_size(get_file_sizes())
