# ruff: isort: skip_file

# start_failure_hook_op_exception
import dagster as dg
import traceback


@dg.failure_hook
def my_failure_hook(context: dg.HookContext):
    op_exception: BaseException = context.op_exception  # type: ignore  # (possible none)
    # print stack trace of exception
    traceback.print_tb(op_exception.__traceback__)


# end_failure_hook_op_exception
