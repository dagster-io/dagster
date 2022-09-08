from dagster import Int, Out, Output, graph, op


@op(
    out={"out_1": Out(Int), "out_2": Out(Int)},
)
def first_op(_context):
    yield Output(1, "out_1")
    yield Output(2, "out_2")


@op(
    out={
        "out_1": Out(Int),
        "out_2": Out(Int),
        "out_3": Out(Int),
        "out_4": Out(Int),
        "out_5": Out(Int),
    },
)
def child_op(_context, input_1, input_2):
    yield Output(input_1, "out_1")
    yield Output(input_1, "out_2")
    yield Output(input_2, "out_3")
    yield Output(input_2, "out_4")
    yield Output(input_2, "out_5")


@op(
    out={
        "out_1": Out(Int),
        "out_2": Out(Int),
        "out_3": Out(Int),
        "out_4": Out(Int),
        "out_5": Out(Int),
    },
)
def child_op_five_inputs(_context, input_1, input_2, input_3, input_4, input_5):
    yield Output(input_1, "out_1")
    yield Output(input_2, "out_2")
    yield Output(input_3, "out_3")
    yield Output(input_4, "out_4")
    yield Output(input_5, "out_5")


@graph(description="Demo graph with many inputs and outputs bound to the same / different ops.")
def multi_inputs_outputs():
    out_1, out_2 = first_op()
    child_op(out_1, out_2)
    c_1, c_2, c_3, c_4, c_5 = child_op(out_1, out_2)
    child_op(c_1, c_3)
    d_1, d_2, d_3, d_4, d_5 = child_op(c_4, c_5)
    child_op_five_inputs(c_1, c_2, c_3, c_4, d_1)
    e_1, e_2, e_3, e_4, e_5 = child_op_five_inputs(d_1, d_2, d_3, d_4, d_5)
    child_op_five_inputs(e_1, e_2, e_3, e_4, e_5)


multi_inputs_outputs_job = multi_inputs_outputs.to_job()
