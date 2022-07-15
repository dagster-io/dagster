from dagster import (
    Field,
)

from dagster.legacy import pipeline
from dagster.core.definitions.events import DynamicOutput
from dagster.core.definitions.output import DynamicOutputDefinition
from dagster.legacy import solid


@solid
def multiply_by_two(context, y):
    context.log.info("echo_again is returning " + str(y * 2))
    return y * 2


@solid(config_schema={"fail_on_first_try": Field(bool, default_value=False)})
def multiply_inputs(context, y, ten):
    if context.solid_config["fail_on_first_try"]:
        current_run = context.instance.get_run_by_id(context.run_id)
        if y == 2 and current_run.parent_run_id is None:
            raise Exception()
    context.log.info("echo is returning " + str(y * ten))
    return y * ten


@solid
def emit_ten(_):
    return 10


@solid
def sum_numbers(_, base, nums):
    return base + sum(nums)


@solid(output_defs=[DynamicOutputDefinition()])
def emit(_):
    for i in range(3):
        yield DynamicOutput(value=i, mapping_key=str(i))


@pipeline
def dynamic_pipeline():
    result = emit().map(lambda num: multiply_by_two(multiply_inputs(num, emit_ten())))
    multiply_by_two.alias("double_total")(sum_numbers(emit_ten(), result.collect()))
