# start_marker
import random

import dagster as dg


@dg.op(
    out={"branch_1": dg.Out(is_required=False), "branch_2": dg.Out(is_required=False)}
)
def branching_op():
    num = random.randint(0, 1)
    if num == 0:
        yield dg.Output(1, "branch_1")
    else:
        yield dg.Output(2, "branch_2")


@dg.op
def branch_1_op(_input):
    pass


@dg.op
def branch_2_op(_input):
    pass


@dg.graph
def branching():
    branch_1, branch_2 = branching_op()
    branch_1_op(branch_1)
    branch_2_op(branch_2)


# end_marker
