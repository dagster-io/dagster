# pylint: disable=unused-argument

import re

from dagster_managed_stacks import ManagedStackDiff
from dagster_managed_stacks.cli import apply, check
from dagster_managed_stacks.utils import diff_dicts

from dagster._utils import file_relative_path

ANSI_ESCAPE = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


def clean_escape(diff: ManagedStackDiff):
    return ANSI_ESCAPE.sub("", str(diff)).strip("\n")


def test_basic_integration(docker_compose_airbyte_instance, airbyte_source_files):
    # First, check that we get the expected diff

    check_result = check(file_relative_path(__file__, "./example_stacks/example_airbyte_stack.py"))

    expected_result = diff_dicts(
        {
            "local-json-input": {
                "url": "/local/sample_file.json",
                "format": "json",
                "provider": {"storage": "local"},
                "dataset_name": "my_data_stream",
            },
            "local-json-output": {
                "destination_path": "./d",
            },
            "local-json-conn": {
                "source": "local-json-input",
                "destination": "local-json-output",
                "normalize data": False,
                "streams": {
                    "my_data_stream": "FULL_REFRESH_APPEND",
                },
            },
        },
        None,
    )

    assert expected_result == check_result

    # Then, apply the diff and check that we get the expected diff again

    apply_result = apply(file_relative_path(__file__, "./example_stacks/example_airbyte_stack.py"))

    assert expected_result == apply_result

    # Now, check that we get no diff after applying the stack

    check_result = check(file_relative_path(__file__, "./example_stacks/example_airbyte_stack.py"))

    assert check_result == ManagedStackDiff()
