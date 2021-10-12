# start_marker
from dagster import Out, fs_io_manager, in_process_executor, job, mem_io_manager, op


@op(out=Out(io_manager_key="fs"))
def op_1():
    return 1


@op(out=Out(io_manager_key="mem"))
def op_2(a):
    return a + 1


@job(resource_defs={"fs": fs_io_manager, "mem": mem_io_manager}, executor_def=in_process_executor)
def my_job():
    op_2(op_1())


# end_marker
