from dagster import execute_pipeline

from ..ge_demo import payroll_data_pipeline


def test_pipeline_success():
    res = execute_pipeline(payroll_data_pipeline, preset='sample_preset_success')
    assert res.success


def test_pipeline_failure():
    res = execute_pipeline(payroll_data_pipeline, preset='sample_preset_fail', raise_on_error=False)
    assert not res.success
