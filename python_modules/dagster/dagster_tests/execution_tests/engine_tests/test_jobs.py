import time

import dagster as dg

from dagster_tests.execution_tests.engine_tests.test_step_delegating_executor import (
    test_step_delegating_executor,
)


@dg.op(out=dg.DynamicOut(str))
def dynamic():
    for x in ["a", "b"]:
        yield dg.DynamicOutput(x, x)


@dg.op(out=dg.Out(is_required=False))
def optional(x):
    if x == "a":
        yield dg.Output(x)


@dg.op
def final(context, xs):
    context.log.info(xs)


def define_dynamic_skipping_job():
    @dg.job(executor_def=test_step_delegating_executor)
    def dynamic_skipping_job():
        xs = dynamic().map(optional)
        xs.map(final)

    return dynamic_skipping_job


@dg.op(out=dg.DynamicOut(int))
def dynamic_output_op():
    for x in range(10):
        yield dg.DynamicOutput(x, str(x))


def define_dynamic_job():
    @dg.job(executor_def=test_step_delegating_executor)
    def dynamic_job():
        dynamic_output_op().map(final)

    return dynamic_job


@dg.op(out={"a": dg.Out(), "b": dg.Out(is_required=False)})
def skipping_op():
    yield dg.Output(1, "a")


@dg.op
def sleep_op():
    time.sleep(15)


def define_skpping_job():
    @dg.job(executor_def=test_step_delegating_executor)
    def skipping_job():
        a, b = skipping_op()
        final(a)
        final(b)
        sleep_op()

    return skipping_job
