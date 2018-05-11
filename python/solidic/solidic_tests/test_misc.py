import pytest

from solidic.definitions import check_valid_name
from solidic.errors import SolidInvalidDefinition


def test_check_valid_name():
    assert check_valid_name('a') == 'a'

    with pytest.raises(SolidInvalidDefinition):
        assert check_valid_name('has a space')

    with pytest.raises(SolidInvalidDefinition):
        assert check_valid_name('')

    with pytest.raises(SolidInvalidDefinition):
        assert check_valid_name('context')
