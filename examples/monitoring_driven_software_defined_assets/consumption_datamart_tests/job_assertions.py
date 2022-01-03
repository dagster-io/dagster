import pytest

from dagster import TextMetadataEntryData


def assert_step_is_successful(node_name, job_result):
    for step_event in job_result.events_for_node(node_name):
        if step_event.is_step_failure:
            failure_data = step_event.step_failure_data.user_failure_data

            if failure_data:
                failure_metadata_str = '\n'.join([
                    f"{m.label} {m.description or ''}: "
                    f"{m.entry_data.text if isinstance(m.entry_data, TextMetadataEntryData) else m.entry_data}"
                    for m in failure_data.metadata_entries
                ])
                failure_details = f"E\t\t{failure_data.description}\nE\t\t{failure_metadata_str}"
            else:
                failure_details = ""

            pytest.fail(f">\t\tFailed: {node_name}\n{failure_details}", pytrace=False)


def assert_step_is_failure(node_name, job_result):
    failed_steps = [step_event for step_event in job_result.events_for_node(node_name) if step_event.is_step_failure]
    if len(failed_steps) == 0:
        pytest.fail(f">\t\t{node_name} should have failed", pytrace=False)
