import pytest
from dagster.utils.backoff import backoff, backoff_delay_generator


class UnretryableException(Exception):
    pass


class RetryableException(Exception):
    pass


class RetryableExceptionB(Exception):
    pass


class Failer:
    def __init__(self, fails=0, exception=RetryableException):
        self.fails = fails
        self.exception = exception
        self.call_count = 0
        self.args = []
        self.kwargs = []

    def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.args.append(args)
        self.kwargs.append(kwargs)

        if self.call_count <= self.fails:
            raise self.exception

        return True


def test_backoff_delay_generator():
    gen = backoff_delay_generator()
    vals = []
    for _ in range(10):
        vals.append(next(gen))

    assert vals == [0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 25.6, 51.2]


def test_backoff():
    fn = Failer(fails=100)
    with pytest.raises(RetryableException):
        backoff(fn, retry_on=(RetryableException,), args=[3, 2, 1], kwargs={"foo": "bar"})

    assert fn.call_count == 5
    assert all([args == (3, 2, 1) for args in fn.args])
    assert all([kwargs == {"foo": "bar"} for kwargs in fn.kwargs])

    fn = Failer()
    assert backoff(fn, retry_on=(RetryableException,), args=[3, 2, 1], kwargs={"foo": "bar"})
    assert fn.call_count == 1

    fn = Failer(fails=1)
    assert backoff(fn, retry_on=(RetryableException,), args=[3, 2, 1], kwargs={"foo": "bar"})
    assert fn.call_count == 2

    fn = Failer(fails=1)
    with pytest.raises(RetryableException):
        backoff(
            fn, retry_on=(RetryableException,), args=[3, 2, 1], kwargs={"foo": "bar"}, max_retries=0
        )
    assert fn.call_count == 1

    fn = Failer(fails=2)
    with pytest.raises(RetryableException):
        backoff(
            fn, retry_on=(RetryableException,), args=[3, 2, 1], kwargs={"foo": "bar"}, max_retries=1
        )
    assert fn.call_count == 2
