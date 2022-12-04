import pytest
from docs_snippets.concepts.configuration.execute_with_config import (
    execute_with_bad_config,
    execute_with_config,
)

from dagster import DagsterInvalidConfigError


def test_run_good_example():
    execute_with_config()


def test_run_bad_example():
    with pytest.raises(DagsterInvalidConfigError):
        execute_with_bad_config()
