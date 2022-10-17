# pylint: disable=unused-argument

import re

from dagster_managed_elements import ManagedElementDiff
from dagster_managed_elements.cli import apply, check
from dagster_managed_elements.utils import diff_dicts

from dagster._utils import file_relative_path


def test_basic_integration(docker_compose_airbyte_instance, airbyte_source_files):
    # First, check that we get the expected diff

    check_result = check(file_relative_path(__file__, "./example_stacks/example_airbyte_stack.py"))

    config_dict = {
        "local-json-input": {
            "url": "/local/sample_file.json",
            "format": "json",
            "provider": {"storage": "local"},
            "dataset_name": "my_data_stream",
        },
        "local-json-output": {
            "destination_path": "/local/destination_file.json",
        },
        "local-json-conn": {
            "source": "local-json-input",
            "destination": "local-json-output",
            "normalize data": False,
            "streams": {
                "my_data_stream": "FULL_REFRESH_APPEND",
            },
        },
    }
    expected_result = diff_dicts(
        config_dict,
        None,
    )

    assert expected_result == check_result

    # Then, apply the diff and check that we get the expected diff again

    apply_result = apply(file_relative_path(__file__, "./example_stacks/example_airbyte_stack.py"))

    assert expected_result == apply_result

    # Now, check that we get no diff after applying the stack

    check_result = check(file_relative_path(__file__, "./example_stacks/example_airbyte_stack.py"))

    assert check_result == ManagedElementDiff()

    # Now, we try to remove everything
    check_result = check(file_relative_path(__file__, "./example_stacks/empty_airbyte_stack.py"))

    # Inverted result (e.g. all deletions)
    expected_result = diff_dicts(
        None,
        config_dict,
    )

    assert expected_result == check_result

    # Then, apply the diff to remove everything and check that we get the expected diff again

    apply_result = apply(file_relative_path(__file__, "./example_stacks/empty_airbyte_stack.py"))

    assert expected_result == apply_result

    # Now, check that we get no diff after applying the stack

    check_result = check(file_relative_path(__file__, "./example_stacks/empty_airbyte_stack.py"))

    assert check_result == ManagedElementDiff()
