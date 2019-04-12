import pytest

from dagster import PipelineDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.utils.test import execute_solids, _unlink_swallow_errors


def test_unlink_swallow_errors():
    _unlink_swallow_errors('32kjhb4kjsbfdkbf.jdfhks83')


def test_execute_solids_with_bad_solid_names():
    with pytest.raises(DagsterInvariantViolationError, match='but that solid was not found'):
        execute_solids(PipelineDefinition([]), [], {'foo': {'bar': 'baz'}})
