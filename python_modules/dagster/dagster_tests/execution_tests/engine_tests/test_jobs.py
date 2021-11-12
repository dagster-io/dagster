import time

from dagster import DynamicOut, Out, job, op
from dagster.core.definitions.events import DynamicOutput, Output

from .test_step_delegating_executor import test_step_delegating_executor


@op(out=DynamicOut(str))
def dynamic():
    for x in ["a", "b"]:
        yield DynamicOutput(x, x)


@op(out=Out(is_required=False))
def optional(x):
    if x == "a":
        yield Output(x)


@op
def final(context, xs):
    context.log.info(xs)


def define_dynamic_skipping_job():
    @job(executor_def=test_step_delegating_executor)
    def dynamic_skipping_job():
        xs = dynamic().map(optional)
        xs.map(final)

    return dynamic_skipping_job


@op(out=DynamicOut(int))
def dynamic_output_op():
    for x in range(10):
        yield DynamicOutput(x, str(x))


def define_dynamic_job():
    @job(executor_def=test_step_delegating_executor)
    def dynamic_job():
        dynamic_output_op().map(final)

    return dynamic_job


@op(out={"a": Out(), "b": Out(is_required=False)})
def skipping_op():
    yield Output(1, "a")


@op
def sleep_op():
    time.sleep(15)


def define_skpping_job():
    @job(executor_def=test_step_delegating_executor)
    def skipping_job():
        a, b = skipping_op()
        final(a)
        final(b)
        sleep_op()

    return skipping_job
