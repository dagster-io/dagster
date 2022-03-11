import pytest
from ge_example.ge_demo import payroll_data

from dagster._utils import file_relative_path


def test_pipeline_success():
    res = payroll_data.execute_in_process()
    assert res.success


def test_pipeline_failure():
    with pytest.raises(ValueError):
        payroll_data.execute_in_process(
            run_config={
                "resources": {
                    "ge_data_context": {
                        "config": {
                            "ge_root_dir": file_relative_path(
                                __file__, "../ge_example/great_expectations"
                            )
                        }
                    }
                },
                "solids": {
                    "read_in_datafile": {
                        "inputs": {
                            "csv_path": {
                                "value": file_relative_path(__file__, "../ge_example/data/fail.csv")
                            }
                        }
                    }
                },
            }
        )
