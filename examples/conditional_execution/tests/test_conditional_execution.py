from unittest import mock

from dagster import execute_pipeline

from ..repo import my_pipeline


def test_conditional_execution():
    with mock.patch("random.randint", return_value=1):
        result = execute_pipeline(my_pipeline)
        assert result.events_by_step_key["branch_2_solid"][0].event_type_value != "STEP_SKIPPED"
        assert result.events_by_step_key["branch_1_solid"][0].event_type_value == "STEP_SKIPPED"
