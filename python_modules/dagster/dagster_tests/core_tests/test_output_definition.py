import re

import mock
import pytest

from dagster import OutputDefinition
from dagster.check import CheckError


def test_output_definition_is_optional_field():
    with mock.patch('warnings.warn'):
        output_definition_onlyopt = OutputDefinition(
            dagster_type=int, name='result', is_optional=True
        )
        assert output_definition_onlyopt.optional is True

    with pytest.raises(
        CheckError,
        match=re.escape('Do not use deprecated "is_optional" now that you are using "is_required"'),
    ):
        OutputDefinition(dagster_type=int, name='result', is_optional=True, is_required=True)


def test_output_definition():
    output_definiton_onlyreq = OutputDefinition(dagster_type=int, name='result', is_required=True)
    assert output_definiton_onlyreq.optional is False

    output_definiton_none = OutputDefinition(dagster_type=int, name='result')
    assert output_definiton_none.optional is False
