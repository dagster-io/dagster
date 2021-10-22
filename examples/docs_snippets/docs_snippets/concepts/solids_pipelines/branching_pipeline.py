# pylint: disable=unused-argument, no-value-for-parameter

# start_marker
import random

from dagster import Out, Output, job, op


@op(out={"branch_1": Out(is_required=False), "branch_2": Out(is_required=False)})
def branching_op():
    num = random.randint(0, 1)
    if num == 0:
        yield Output(1, "branch_1")
    else:
        yield Output(2, "branch_2")


@op
def branch_1_op(_input):
    pass


@op
def branch_2_op(_input):
    pass


@job
def branching():
    branch_1, branch_2 = branching_op()
    branch_1_op(branch_1)
    branch_2_op(branch_2)


# end_marker
