import time

from dagster import Int, Output, RetryRequested, VersionStrategy, job
from dagster._core.definitions.decorators import op
from dagster._core.definitions.output import Out
from dagster._core.test_utils import nesting_graph
from dagster_celery import celery_executor

# test_execute jobs


@op
def simple(_):
    return 1


@op
def add_one(_, num):
    return num + 1


@job(executor_def=celery_executor)
def test_job():
    simple()


@job(executor_def=celery_executor)
def test_serial_job():
    add_one(simple())


@op(out={"value_one": Out(), "value_two": Out()})
def emit_values(_context):
    yield Output(1, "value_one")
    yield Output(2, "value_two")


@op
def subtract(num_one, num_two):
    return num_one - num_two


@job(executor_def=celery_executor)
def test_diamond_job():
    value_one, value_two = emit_values()
    subtract(num_one=add_one(num=value_one), num_two=add_one.alias("renamed")(num=value_two))


@job(executor_def=celery_executor)
def test_parallel_job():
    value = simple()
    for i in range(10):
        add_one.alias("add_one_" + str(i))(value)


COMPOSITE_DEPTH = 3


def composite_job():
    return nesting_graph(COMPOSITE_DEPTH, 2).to_job(executor_def=celery_executor)


@op(
    out={
        "out_1": Out(Int, is_required=False),
        "out_2": Out(Int, is_required=False),
        "out_3": Out(Int, is_required=False),
    }
)
def foo(_):
    yield Output(1, "out_1")


@op
def bar(_, input_arg):
    return input_arg


@job(executor_def=celery_executor)
def test_optional_outputs():
    foo_res = foo()
    bar.alias("first_consumer")(input_arg=foo_res.out_1)
    bar.alias("second_consumer")(input_arg=foo_res.out_2)
    bar.alias("third_consumer")(input_arg=foo_res.out_3)


@op
def fails():
    raise Exception("argjhgjh")


@op
def should_never_execute(foo):
    assert False  # should never execute


@job(executor_def=celery_executor)
def test_fails():
    should_never_execute(fails())


@op
def retry_request():
    raise RetryRequested()


@job(executor_def=celery_executor)
def test_retries():
    retry_request()


@op(config_schema=str)
def destroy(context, x):
    raise ValueError()


@job(executor_def=celery_executor)
def engine_error():
    a = simple()
    b = destroy(a)

    subtract(a, b)


@op(
    tags={
        "dagster-k8s/resource_requirements": {
            "requests": {"cpu": "250m", "memory": "64Mi"},
            "limits": {"cpu": "500m", "memory": "2560Mi"},
        }
    }
)
def resource_req_op(context):
    context.log.info("running")


@job(executor_def=celery_executor)
def test_resources_limit():
    resource_req_op()


# test_priority jobs


@op(tags={"dagster-celery/priority": 0})
def zero(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "0"
    context.log.info("Executing with priority 0")
    return True


@op(tags={"dagster-celery/priority": 1})
def one(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "1"
    context.log.info("Executing with priority 1")
    return True


@op(tags={"dagster-celery/priority": 2})
def two(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "2"
    context.log.info("Executing with priority 2")
    return True


@op(tags={"dagster-celery/priority": 3})
def three(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "3"
    context.log.info("Executing with priority 3")
    return True


@op(tags={"dagster-celery/priority": 4})
def four(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "4"
    context.log.info("Executing with priority 4")
    return True


@op(tags={"dagster-celery/priority": 5})
def five(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "5"
    context.log.info("Executing with priority 5")
    return True


@op(tags={"dagster-celery/priority": 6})
def six(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "6"
    context.log.info("Executing with priority 6")
    return True


@op(tags={"dagster-celery/priority": 7})
def seven_(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "7"
    context.log.info("Executing with priority 7")
    return True


@op(tags={"dagster-celery/priority": 8})
def eight(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "8"
    context.log.info("Executing with priority 8")
    return True


@op(tags={"dagster-celery/priority": 9})
def nine(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "9"
    context.log.info("Executing with priority 9")
    return True


@op(tags={"dagster-celery/priority": 10})
def ten(context):
    assert "dagster-celery/priority" in context.op.tags
    assert context.op.tags["dagster-celery/priority"] == "10"
    context.log.info("Executing with priority 10")
    return True


@job(executor_def=celery_executor)
def priority_job():
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


@job(executor_def=celery_executor)
def simple_priority_job():
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


@op
def sleep_op(_):
    time.sleep(0.5)
    return True


@job(executor_def=celery_executor)
def low_job():
    sleep_op.alias("low_one")()
    sleep_op.alias("low_two")()
    sleep_op.alias("low_three")()
    sleep_op.alias("low_four")()
    sleep_op.alias("low_five")()


@job(executor_def=celery_executor)
def hi_job():
    sleep_op.alias("hi_one")()
    sleep_op.alias("hi_two")()
    sleep_op.alias("hi_three")()
    sleep_op.alias("hi_four")()
    sleep_op.alias("hi_five")()


@job(executor_def=celery_executor)
def interrupt_job():
    for i in range(50):
        sleep_op.alias("sleep_" + str(i))()


# test_queues jobs


@op(tags={"dagster-celery/queue": "fooqueue"})
def fooqueue(context):
    assert context.solid.tags["dagster-celery/queue"] == "fooqueue"
    context.log.info("Executing on queue fooqueue")
    return True


@job(executor_def=celery_executor)
def multiqueue_job():
    fooqueue()


@op
def bar_solid():
    return "bar"


class BasicVersionStrategy(VersionStrategy):
    def get_op_version(self, _):
        return "bar"


@job(
    executor_def=celery_executor,
    version_strategy=BasicVersionStrategy(),
)
def bar_job():
    bar_solid()
