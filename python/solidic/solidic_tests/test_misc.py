import pytest

from solidic.definitions import (check_valid_name, has_context_variable)
from solidic.errors import SolidInvalidDefinition


def test_check_valid_name():
    assert check_valid_name('a') == 'a'

    with pytest.raises(SolidInvalidDefinition):
        assert check_valid_name('has a space')

    with pytest.raises(SolidInvalidDefinition):
        assert check_valid_name('')

    with pytest.raises(SolidInvalidDefinition):
        assert check_valid_name('context')


def test_has_context_variable():
    # pylint: disable=W0613

    def nope(_foo):
        pass

    def yup(context, _bar):
        pass

    assert not has_context_variable(nope)
    assert has_context_variable(yup)
    assert not has_context_variable(lambda: None)
    assert not has_context_variable(lambda bar: None)
    assert has_context_variable(lambda context: None)
    assert has_context_variable(lambda bar, context: None)
