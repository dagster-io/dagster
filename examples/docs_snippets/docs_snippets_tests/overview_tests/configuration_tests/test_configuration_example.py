import pytest
from docs_snippets.overview.configuration.example import (
    run_bad_example,
    run_good_example,
    run_other_bad_example,
)

from dagster import DagsterInvalidConfigError


def test_config_example():
    assert run_good_example().success

    with pytest.raises(DagsterInvalidConfigError):
        run_bad_example()

    with pytest.raises(DagsterInvalidConfigError):
        run_other_bad_example()
