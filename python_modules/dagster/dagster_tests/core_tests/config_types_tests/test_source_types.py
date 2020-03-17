import os

from dagster import IntSource, StringSource
from dagster.config.validate import process_config
from dagster.core.test_utils import environ


def test_string_source():
    assert process_config(StringSource, 'foo').success
    assert not process_config(StringSource, 1).success

    assert not process_config(StringSource, {'env': 1}).success

    assert 'DAGSTER_TEST_ENV_VAR' not in os.environ
    assert not process_config(StringSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).success

    assert (
        'Environment variable "DAGSTER_TEST_ENV_VAR" is not set'
        in process_config(StringSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).errors[0].message
    )

    with environ({'DAGSTER_TEST_ENV_VAR': 'baz'}):
        assert process_config(StringSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).success
        assert process_config(StringSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).value == 'baz'


def test_int_source():
    assert process_config(IntSource, 1).success
    assert not process_config(IntSource, 'foo').success

    assert not process_config(IntSource, {'env': 1}).success

    assert 'DAGSTER_TEST_ENV_VAR' not in os.environ
    assert not process_config(IntSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).success

    assert (
        'Environment variable "DAGSTER_TEST_ENV_VAR" is not set'
        in process_config(IntSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).errors[0].message
    )

    with environ({'DAGSTER_TEST_ENV_VAR': '4'}):
        assert process_config(IntSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).success
        assert process_config(IntSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).value == 4

    with environ({'DAGSTER_TEST_ENV_VAR': 'four'}):
        assert not process_config(IntSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).success
        assert (
            "invalid literal for int() with base 10: 'four'"
            in process_config(IntSource, {'env': 'DAGSTER_TEST_ENV_VAR'}).errors[0].message
        )
