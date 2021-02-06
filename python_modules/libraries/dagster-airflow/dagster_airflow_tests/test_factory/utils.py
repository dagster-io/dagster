from airflow.exceptions import AirflowSkipException
from dagster.core.events.log import EventRecord


def validate_pipeline_execution(pipeline_exc_result):
    expected_airflow_demo_events = {
        ("STEP_START", "multiply_the_word"),
        ("STEP_INPUT", "multiply_the_word"),
        ("STEP_OUTPUT", "multiply_the_word"),
        ("HANDLED_OUTPUT", "multiply_the_word"),
        ("STEP_SUCCESS", "multiply_the_word"),
        ("STEP_START", "count_letters"),
        ("LOADED_INPUT", "count_letters"),
        ("STEP_INPUT", "count_letters"),
        ("STEP_OUTPUT", "count_letters"),
        ("STEP_SUCCESS", "count_letters"),
    }

    seen_events = set()
    for result in pipeline_exc_result.values():
        for event in result:
            if isinstance(event, EventRecord):
                seen_events.add((event.dagster_event.event_type_value, event.step_key))
            else:
                seen_events.add((event.event_type_value, event.step_key))

    # there may be additional engine events for resources when present
    # just ensure we saw of what we expected
    assert expected_airflow_demo_events.difference(seen_events) == set()


def validate_skip_pipeline_execution(result):
    expected_airflow_task_states = {
        ("foo", False),
        ("first_consumer", False),
        ("second_consumer", True),
        ("third_consumer", True),
    }

    seen_events = {
        (ti.task_id, isinstance(value, AirflowSkipException)) for ti, value in result.items()
    }
    assert seen_events == expected_airflow_task_states
