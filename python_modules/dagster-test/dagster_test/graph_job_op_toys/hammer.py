import random
import time

from dagster import Field, In, Out, Output, graph, op


@op(
    ins={"chase_duration": In(int)},
    out=Out(int),
    config_schema={
        "chase_size": Field(
            int,
            default_value=100000,
            is_required=False,
            description="How big should the pointer chase array be?",
        )
    },
)
def hammer_op(context, chase_duration):
    """what better way to do a lot of gnarly work than to pointer chase?"""
    ptr_length = context.op_config["chase_size"]

    data = list(range(0, ptr_length))
    random.shuffle(data)

    curr = random.randint(0, ptr_length - 1)
    # and away we go
    start_time = time.time()
    while (time.time() - start_time) < chase_duration:
        curr = data[curr]

    context.log.info("Hammered - start %d end %d" % (start_time, time.time()))
    return chase_duration


@op(
    config_schema=Field(int, is_required=False, default_value=1),
    out={"out_1": Out(int), "out_2": Out(int), "out_3": Out(int), "out_4": Out(int)},
)
def chase_giver(context):
    chase_duration = context.op_config

    yield Output(chase_duration, "out_1")
    yield Output(chase_duration, "out_2")
    yield Output(chase_duration, "out_3")
    yield Output(chase_duration, "out_4")


@op(
    ins={"in_1": In(int), "in_2": In(int), "in_3": In(int), "in_4": In(int)},
    out=Out(int),
)
def reducer(_, in_1, in_2, in_3, in_4):
    return in_1 + in_2 + in_3 + in_4


@graph
def hammer():
    out_1, out_2, out_3, out_4 = chase_giver()
    reducer(
        in_1=hammer_op(chase_duration=out_1),
        in_2=hammer_op(chase_duration=out_2),
        in_3=hammer_op(chase_duration=out_3),
        in_4=hammer_op(chase_duration=out_4),
    )


hammer_default_executor_job = hammer.to_job()
