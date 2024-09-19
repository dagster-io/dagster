from dagster import Definitions, load_assets_from_modules, mem_io_manager
from dagster_test.toys import basic_assets


def test_basic_assets_job():
    Definitions(
        jobs=[basic_assets.basic_assets_job], assets=load_assets_from_modules([basic_assets])
    ).get_job_def("basic_assets_job").execute_in_process(resources={"io_manager": mem_io_manager})
