from airflow.exceptions import AirflowSkipException

from dagster.core.events.log import DagsterEventRecord


def validate_pipeline_execution(pipeline_exc_result):
    expected_airflow_demo_events = {
        ('ENGINE_EVENT', 'multiply_the_word.compute'),
        ('STEP_START', 'multiply_the_word.compute'),
        ('STEP_INPUT', 'multiply_the_word.compute'),
        ('STEP_OUTPUT', 'multiply_the_word.compute'),
        ('OBJECT_STORE_OPERATION', 'multiply_the_word.compute'),
        ('STEP_SUCCESS', 'multiply_the_word.compute'),
        ('ENGINE_EVENT', 'count_letters.compute'),
        ('STEP_START', 'count_letters.compute'),
        ('OBJECT_STORE_OPERATION', 'count_letters.compute'),
        ('STEP_INPUT', 'count_letters.compute'),
        ('STEP_OUTPUT', 'count_letters.compute'),
        ('STEP_SUCCESS', 'count_letters.compute'),
    }

    seen_events = set()
    for result in pipeline_exc_result.values():
        for event in result:
            if isinstance(event, DagsterEventRecord):
                seen_events.add((event.dagster_event.event_type_value, event.step_key))
            else:
                seen_events.add((event.event_type_value, event.step_key))

    assert seen_events == expected_airflow_demo_events


def validate_skip_pipeline_execution(result):
    expected_airflow_task_states = {
        ('foo', False),
        ('first_consumer', False),
        ('second_consumer', True),
        ('third_consumer', True),
    }

    seen_events = {
        (ti.task_id, isinstance(value, AirflowSkipException)) for ti, value in result.items()
    }
    assert seen_events == expected_airflow_task_states
