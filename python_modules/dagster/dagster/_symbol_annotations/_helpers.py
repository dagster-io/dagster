from dagster._core.decorator_utils import is_resource_def
from dagster._symbol_annotations.annotatable import Annotatable


def _get_warning_stacklevel(obj: Annotatable):
    """Get the stacklevel to use for warnings that are attached to a target via decorator.

    The goal is to have the warning point to the line where the function in the
    underlying object is actually invoked. This isn't straightforward
    because some objects have complicated logic in between `__call__` and
    the site at which a wrapped function containing the warning is actually
    called. Can be determined through trial and error.
    """
    if is_resource_def(obj):
        return 6
    else:
        return 4
