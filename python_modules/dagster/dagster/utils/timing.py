from contextlib import contextmanager
import time

from dagster import check


class TimerResult(object):
    def __init__(self):
        self.start_time = time.time()
        self.end_time = None

    @property
    def seconds(self):
        check.invariant(self.end_time is not None, 'end time is not set')
        return self.end_time - self.start_time

    @property
    def millis(self):
        return self.seconds * 1000


@contextmanager
def time_execution_scope():
    '''Usage:

    from solid_util.timing import time_execution_scope
    with time_execution_scope() as timer_result:
        do_some_operation()
    print('do_some_operation took {timer_result.millis} milliseconds'.format(timer_result=timer_result))
    '''

    timer_result = TimerResult()
    yield timer_result
    timer_result.end_time = time.time()
