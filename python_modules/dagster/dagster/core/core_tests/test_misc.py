import pytest

from dagster.core.definitions import check_valid_name
from dagster.core.errors import DagsterInvalidDefinitionError


def test_check_valid_name():
    assert check_valid_name('a') == 'a'

    with pytest.raises(DagsterInvalidDefinitionError):
        assert check_valid_name('has a space')

    with pytest.raises(DagsterInvalidDefinitionError):
        assert check_valid_name('')

    with pytest.raises(DagsterInvalidDefinitionError):
        assert check_valid_name('context')
