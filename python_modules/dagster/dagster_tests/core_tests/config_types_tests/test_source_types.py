import os

from dagster.config.validate import process_config
from dagster.core.instance.source_types import StringSource
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
