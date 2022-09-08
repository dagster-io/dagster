import sys

from dagster_dask import dask_executor

from dagster import job
from dagster._utils import file_relative_path

sys.path.append(file_relative_path(__file__, "../../../dagster-test/dagster_test/toys"))
from hammer import hammer  # pylint: disable=import-error


@job(executor_def=dask_executor)
def hammer_job():
    hammer()
