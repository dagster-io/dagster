from typing import Any, Dict

import pytest
from dagster import DagsterInvalidConfigError, job, op


def test_dict_input():
    @op
    def the_op(x: dict[str, str]):
        assert x == {"foo": "bar"}

    @job
    def the_job():
        the_op()

    assert the_job.execute_in_process(
        run_config={
            "ops": {
                "the_op": {
                    "inputs": {
                        "x": {
                            "foo": "bar",
                        },
                    }
                }
            }
        }
    ).success

    @job
    def the_job_top_lvl_input(x):
        the_op(x)

    assert the_job_top_lvl_input.execute_in_process(
        run_config={"inputs": {"x": {"foo": "bar"}}}
    ).success


def test_any_dict_input():
    @op
    def the_op(x: dict[str, Any]):
        assert x == {"foo": "bar"}

    @job
    def the_job():
        the_op()

    assert the_job.execute_in_process(
        run_config={
            "ops": {
                "the_op": {
                    "inputs": {
                        "x": {
                            "foo": {"value": "bar"},
                        },
                    }
                }
            }
        }
    ).success

    @job
    def the_job_top_lvl_input(x):
        the_op(x)

    assert the_job_top_lvl_input.execute_in_process(
        run_config={"inputs": {"x": {"foo": {"value": "bar"}}}}
    ).success


def test_malformed_input_schema_dict():
    @op
    def the_op(_x: dict[str, Any]):
        pass

    @job
    def the_job(x):
        the_op(x)

    # Case: I specify a dict input, and I try to pass a string to the Any parameter.
    with pytest.raises(DagsterInvalidConfigError):
        the_job.execute_in_process(run_config={"inputs": {"x": {"foo": "bar"}}})

    # Case: I specify a dict input, and I try to pass a dictionary to the Any parameter (but not an input schema dictionary)
    with pytest.raises(DagsterInvalidConfigError):
        the_job.execute_in_process(run_config={"inputs": {"x": {"foo": {"foo": "bar"}}}})
