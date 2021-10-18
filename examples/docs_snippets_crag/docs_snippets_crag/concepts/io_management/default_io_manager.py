from dagster import fs_io_manager, job, op


@op
def op_1():
    return 1


@op
def op_2(a):
    return a + 1


@job(resource_defs={"io_manager": fs_io_manager})
def my_job():
    op_2(op_1())
