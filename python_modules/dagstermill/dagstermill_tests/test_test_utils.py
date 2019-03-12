from dagstermill import DagstermillError
from dagstermill.test_utils import notebook_test


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
