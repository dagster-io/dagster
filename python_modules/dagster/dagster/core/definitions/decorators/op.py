from dagster.utils.backcompat import experimental_decorator

from .solid import solid


@experimental_decorator
def op(*args, **kwargs):
    return solid(*args, **kwargs)
