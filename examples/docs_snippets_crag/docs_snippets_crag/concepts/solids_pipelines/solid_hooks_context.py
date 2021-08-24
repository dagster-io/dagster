"""isort:skip_file"""

# start_failure_hook_solid_exception
from dagster import HookContext, failure_hook
import traceback


@failure_hook
def my_failure_hook(context: HookContext):
    solid_exception: BaseException = context.solid_exception
    # print stack trace of exception
    traceback.print_tb(solid_exception.__traceback__)


# end_failure_hook_solid_exception
