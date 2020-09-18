import sys
import textwrap

from dagster import DagsterEvent
from dagster.core.definitions.dependency import SolidHandle
from dagster.core.execution.plan.objects import StepFailureData, StepOutputData, StepOutputHandle
from dagster.core.log_manager import construct_log_string
from dagster.utils.error import serializable_error_info_from_exc_info


def test_construct_log_string_for_event():
    step_output_event = DagsterEvent(
        event_type_value="STEP_OUTPUT",
        pipeline_name="my_pipeline",
        step_key="solid2.compute",
        solid_handle=SolidHandle("solid2", None),
        step_kind_value="COMPUTE",
        logging_tags={},
        event_specific_data=StepOutputData(
            step_output_handle=StepOutputHandle("solid2.compute", "result")
        ),
        message='Yielded output "result" of type "Any" for step "solid2.compute". (Type check passed).',
        pid=54348,
    )
    message_props = {"dagster_event": step_output_event, "pipeline_name": "my_pipeline"}

    synth_props = {
        "orig_message": step_output_event.message,
        "run_id": "f79a8a93-27f1-41b5-b465-b35d0809b26d",
    }
    assert (
        construct_log_string(message_props=message_props, logging_tags={}, synth_props=synth_props)
        == 'my_pipeline - f79a8a93-27f1-41b5-b465-b35d0809b26d - 54348 - STEP_OUTPUT - Yielded output "result" of type "Any" for step "solid2.compute". (Type check passed).'
    )


def test_construct_log_string_for_log():
    message_props = {"pipeline_name": "my_pipeline"}

    synth_props = {
        "orig_message": "hear my tale",
        "run_id": "f79a8a93-27f1-41b5-b465-b35d0809b26d",
    }
    assert (
        construct_log_string(message_props=message_props, logging_tags={}, synth_props=synth_props)
        == "my_pipeline - f79a8a93-27f1-41b5-b465-b35d0809b26d - hear my tale"
    )


def test_construct_log_string_with_error():
    try:
        raise ValueError("some error")
    except ValueError:
        error = serializable_error_info_from_exc_info(sys.exc_info())

    step_failure_event = DagsterEvent(
        event_type_value="STEP_FAILURE",
        pipeline_name="my_pipeline",
        step_key="solid2.compute",
        solid_handle=SolidHandle("solid2", None),
        step_kind_value="COMPUTE",
        logging_tags={},
        event_specific_data=StepFailureData(error=error, user_failure_data=None),
        message='Execution of step "solid2.compute" failed.',
        pid=54348,
    )

    message_props = {"dagster_event": step_failure_event, "pipeline_name": "my_pipeline"}

    synth_props = {
        "orig_message": step_failure_event.message,
        "run_id": "f79a8a93-27f1-41b5-b465-b35d0809b26d",
    }
    log_string = construct_log_string(
        message_props=message_props, logging_tags={}, synth_props=synth_props
    )
    expected_start = textwrap.dedent(
        """
        my_pipeline - f79a8a93-27f1-41b5-b465-b35d0809b26d - 54348 - STEP_FAILURE - Execution of step "solid2.compute" failed.

        ValueError: some error

          File "
        """
    ).strip()
    assert log_string.startswith(expected_start)
