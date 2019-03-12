import pytest

from dagstermill import DagstermillError
from dagstermill.test_utils import notebook_test


def test_normal_test():
    has_been_called = {}

    @notebook_test
    def normal_test():
        has_been_called['yup'] = True
        assert True

    normal_test()

    assert 'yup' in has_been_called


def test_retry_logic():
    has_been_called = {'times': 0}

    @notebook_test
    def execute_thing():
        has_been_called['times'] = has_been_called['times'] + 1
        if 'yup' not in has_been_called:
            has_been_called['yup'] = True
            raise DagstermillError('Kernel died before replying to kernel_info')

    execute_thing()

    assert has_been_called['yup']
    assert has_been_called['times'] == 2


def test_double_fail():
    has_been_called = {'times': 0}

    @notebook_test
    def always_fail():
        has_been_called['times'] = has_been_called['times'] + 1
        raise DagstermillError('Kernel died before replying to kernel_info')

    with pytest.raises(DagstermillError):
        always_fail()

    assert has_been_called['times'] == 2

