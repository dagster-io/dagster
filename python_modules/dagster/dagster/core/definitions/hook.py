from collections import namedtuple

from dagster import check


class HookDefinition(namedtuple('_HookDefinition', 'name hook_fn required_resource_keys')):
    '''Define a hook which can be triggered during a solid execution (e.g. a callback on the step
    execution failure event during a solid execution).

    Args:
        name (str): The name of this hook.
        hook_fn (Callable): The callback function that will be triggered.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            hook.
    '''

    def __new__(cls, name, hook_fn, required_resource_keys=None):
        return super(HookDefinition, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            hook_fn=check.callable_param(hook_fn, 'hook_fn'),
            required_resource_keys=frozenset(
                check.opt_set_param(required_resource_keys, 'required_resource_keys', of_type=str)
            ),
        )
