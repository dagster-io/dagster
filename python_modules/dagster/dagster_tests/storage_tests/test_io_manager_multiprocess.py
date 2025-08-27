import dagster as dg
from dagster import multiprocess_executor


@dg.op
def op_a(_context):
    return [1, 2, 3]


@dg.op
def op_b(_context, _df):
    return 1


@dg.job(executor_def=multiprocess_executor)
def my_job():
    op_b(op_a())


def test_io_manager_with_multi_process_executor():
    with dg.instance_for_test() as instance:
        with dg.execute_job(dg.reconstructable(my_job), instance=instance) as result:
            assert result.success
            assert result.output_for_node("op_b") == 1
            assert result.output_for_node("op_a") == [1, 2, 3]
