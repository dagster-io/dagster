# isort: skip_file

# start_failure_hook_op_exception
from dagster import HookContext, failure_hook
import traceback


@failure_hook
def my_failure_hook(context: HookContext):
    op_exception: BaseException = context.op_exception
    # print stack trace of exception
    traceback.print_tb(op_exception.__traceback__)


# end_failure_hook_op_exception
