import pytest
from dagster import RunConfig
from dagster._utils import file_relative_path
from dagster_ge.factory import GEContextResource

from with_great_expectations import defs
from with_great_expectations.ge_demo import GEOpConfig, payroll_data


def test_pipeline_success():
    res = payroll_data.execute_in_process(
        resources={
            "ge_data_context": GEContextResource(
                ge_root_dir=file_relative_path(
                    __file__, "../with_great_expectations/great_expectations"
                )
            )
        },
    )
    assert res.success


def test_pipeline_failure():
    with pytest.raises(ValueError):
        payroll_data.execute_in_process(
            resources={
                "ge_data_context": GEContextResource(
                    ge_root_dir=file_relative_path(
                        __file__, "../with_great_expectations/great_expectations"
                    )
                )
            },
            run_config=RunConfig(
                {
                    "read_in_datafile": GEOpConfig(
                        csv_path=file_relative_path(
                            __file__, "../with_great_expectations/data/fail.csv"
                        )
                    )
                }
            ),
        )


def test_defs_can_load():
    assert defs.get_job_def("payroll_data")
