from dagster import In, Nothing, job, op


@op
def op_with_nothing_output() -> None:
    ...


@op(ins={"in1": In(Nothing)})
def op_with_nothing_input() -> None:
    ...


@job
def nothing_job():
    # pylint: disable=E1121
    op_with_nothing_input(op_with_nothing_output())
