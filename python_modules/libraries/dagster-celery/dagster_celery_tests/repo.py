import time

from dagster import (
    InputDefinition,
    Int,
    ModeDefinition,
    Output,
    OutputDefinition,
    RetryRequested,
    default_executors,
    lambda_solid,
    pipeline,
    solid,
)
from dagster.core.test_utils import nesting_composite_pipeline
from dagster_celery import celery_executor

celery_mode_defs = [ModeDefinition(executor_defs=default_executors + [celery_executor])]


# test_execute pipelines


@solid
def simple(_):
    return 1


@solid
def add_one(_, num):
    return num + 1


@pipeline(mode_defs=celery_mode_defs)
def test_pipeline():
    return simple()


@pipeline(mode_defs=celery_mode_defs)
def test_serial_pipeline():
    return add_one(simple())


@solid(output_defs=[OutputDefinition(name="value_one"), OutputDefinition(name="value_two")])
def emit_values(_context):
    yield Output(1, "value_one")
    yield Output(2, "value_two")


@lambda_solid(input_defs=[InputDefinition("num_one"), InputDefinition("num_two")])
def subtract(num_one, num_two):
    return num_one - num_two


@pipeline(mode_defs=celery_mode_defs)
def test_diamond_pipeline():
    value_one, value_two = emit_values()
    return subtract(num_one=add_one(num=value_one), num_two=add_one.alias("renamed")(num=value_two))


@pipeline(mode_defs=celery_mode_defs)
def test_parallel_pipeline():
    value = simple()
    for i in range(10):
        add_one.alias("add_one_" + str(i))(value)


COMPOSITE_DEPTH = 3


def composite_pipeline():
    return nesting_composite_pipeline(COMPOSITE_DEPTH, 2, mode_defs=celery_mode_defs)


@solid(
    output_defs=[
        OutputDefinition(Int, "out_1", is_required=False),
        OutputDefinition(Int, "out_2", is_required=False),
        OutputDefinition(Int, "out_3", is_required=False),
    ]
)
def foo(_):
    yield Output(1, "out_1")


@solid
def bar(_, input_arg):
    return input_arg


@pipeline(mode_defs=celery_mode_defs)
def test_optional_outputs():
    # pylint: disable=no-member
    foo_res = foo()
    bar.alias("first_consumer")(input_arg=foo_res.out_1)
    bar.alias("second_consumer")(input_arg=foo_res.out_2)
    bar.alias("third_consumer")(input_arg=foo_res.out_3)


@lambda_solid
def fails():
    raise Exception("argjhgjh")


@lambda_solid
def should_never_execute(_):
    assert False  # should never execute


@pipeline(mode_defs=celery_mode_defs)
def test_fails():
    should_never_execute(fails())


@lambda_solid
def retry_request():
    raise RetryRequested()


@pipeline(mode_defs=celery_mode_defs)
def test_retries():
    retry_request()


@solid(config_schema=str)
def destroy(context, x):
    raise ValueError()


@pipeline(mode_defs=celery_mode_defs)
def engine_error():
    a = simple()
    b = destroy(a)

    subtract(a, b)


@solid(
    tags={
        "dagster-k8s/resource_requirements": {
            "requests": {"cpu": "250m", "memory": "64Mi"},
            "limits": {"cpu": "500m", "memory": "2560Mi"},
        }
    }
)
def resource_req_solid(context):
    context.log.info("running")


@pipeline(mode_defs=celery_mode_defs)
def test_resources_limit():
    resource_req_solid()


# test_priority pipelines


@solid(tags={"dagster-celery/priority": 0})
def zero(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "0"
    context.log.info("Executing with priority 0")
    return True


@solid(tags={"dagster-celery/priority": 1})
def one(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "1"
    context.log.info("Executing with priority 1")
    return True


@solid(tags={"dagster-celery/priority": 2})
def two(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "2"
    context.log.info("Executing with priority 2")
    return True


@solid(tags={"dagster-celery/priority": 3})
def three(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "3"
    context.log.info("Executing with priority 3")
    return True


@solid(tags={"dagster-celery/priority": 4})
def four(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "4"
    context.log.info("Executing with priority 4")
    return True


@solid(tags={"dagster-celery/priority": 5})
def five(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "5"
    context.log.info("Executing with priority 5")
    return True


@solid(tags={"dagster-celery/priority": 6})
def six(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "6"
    context.log.info("Executing with priority 6")
    return True


@solid(tags={"dagster-celery/priority": 7})
def seven_(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "7"
    context.log.info("Executing with priority 7")
    return True


@solid(tags={"dagster-celery/priority": 8})
def eight(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "8"
    context.log.info("Executing with priority 8")
    return True


@solid(tags={"dagster-celery/priority": 9})
def nine(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "9"
    context.log.info("Executing with priority 9")
    return True


@solid(tags={"dagster-celery/priority": 10})
def ten(context):
    assert "dagster-celery/priority" in context.solid.tags
    assert context.solid.tags["dagster-celery/priority"] == "10"
    context.log.info("Executing with priority 10")
    return True


@pipeline(mode_defs=celery_mode_defs)
def priority_pipeline():
    for i in range(50):
        zero.alias("zero_" + str(i))()
        one.alias("one_" + str(i))()
        two.alias("two_" + str(i))()
        three.alias("three_" + str(i))()
        four.alias("four_" + str(i))()
        five.alias("five_" + str(i))()
        six.alias("six_" + str(i))()
        seven_.alias("seven_" + str(i))()
        eight.alias("eight_" + str(i))()
        nine.alias("nine" + str(i))()
        ten.alias("ten_" + str(i))()


@pipeline(mode_defs=celery_mode_defs)
def simple_priority_pipeline():
    zero()
    one()
    two()
    three()
    four()
    five()
    six()
    seven_()
    eight()
    nine()
    ten()


@solid
def sleep_solid(_):
    time.sleep(0.5)
    return True


@pipeline(mode_defs=celery_mode_defs)
def low_pipeline():
    sleep_solid.alias("low_one")()
    sleep_solid.alias("low_two")()
    sleep_solid.alias("low_three")()
    sleep_solid.alias("low_four")()
    sleep_solid.alias("low_five")()


@pipeline(mode_defs=celery_mode_defs)
def hi_pipeline():
    sleep_solid.alias("hi_one")()
    sleep_solid.alias("hi_two")()
    sleep_solid.alias("hi_three")()
    sleep_solid.alias("hi_four")()
    sleep_solid.alias("hi_five")()


@pipeline(mode_defs=celery_mode_defs)
def interrupt_pipeline():
    for i in range(50):
        sleep_solid.alias("sleep_" + str(i))()


# test_queues pipelines


@solid(tags={"dagster-celery/queue": "fooqueue"})
def fooqueue(context):
    assert context.solid.tags["dagster-celery/queue"] == "fooqueue"
    context.log.info("Executing on queue fooqueue")
    return True


@pipeline(mode_defs=celery_mode_defs)
def multiqueue_pipeline():
    fooqueue()
