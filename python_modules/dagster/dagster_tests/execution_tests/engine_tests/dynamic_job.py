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
