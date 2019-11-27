from functools import update_wrapper

from dagster import check
from dagster.core.execution.config import InProcessExecutorConfig, MultiprocessExecutorConfig
from dagster.core.types import Field, Int
from dagster.core.types.field_utils import check_user_facing_opt_field_param

from .config import resolve_config_field


class ExecutorDefinition(object):
    '''
    Args:
        name (Optional[str]): The name of the executor.
        config_field (Optional[Field]): Used in the rare case of a top level config type other than
            a dictionary. Only one of ``config`` or ``config_field`` may be set.
        executor_creation_fn(Optional[Callable]): Should accept an :py:class:`InitExecutorContext`
            and return an instance of :py:class:`ExecutorConfig`.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            executor.

    '''

    def __init__(
        self, name, config_field=None, executor_creation_fn=None, required_resource_keys=None
    ):
        self._name = check.str_param(name, 'name')
        self._config_field = check_user_facing_opt_field_param(
            config_field,
            'config_field',
            'of an ExecutorDefinition named {name}'.format(name=self.name),
        )
        self._executor_creation_fn = check.opt_callable_param(
            executor_creation_fn, 'executor_creation_fn'
        )
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, 'required_resource_keys', of_type=str
        )

    @property
    def name(self):
        return self._name

    @property
    def config_field(self):
        return self._config_field

    @property
    def executor_creation_fn(self):
        return self._executor_creation_fn

    @property
    def required_resource_keys(self):
        return self._required_resource_keys


def executor(name=None, config_field=None, config=None, required_resource_keys=None):
    '''Define an executor.
    
    The decorated function should accept an :py:class:`InitExecutorContext` and return an instance
    of :py:class:`ExecutorConfig`.

    Args:
        name (Optional[str]): The name of the executor.
        config (Dict[str, Field]): The schema for the configuration data to be made available to
            the decorated function.
        config_field (Optional[Field]): Used in the rare case of a top level config type other than
            a dictionary. Only one of ``config`` or ``config_field`` may be set.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            executor.
    '''
    if callable(name):
        check.invariant(config_field is None)
        check.invariant(config is None)
        check.invariant(required_resource_keys is None)
        return _ExecutorDecoratorCallable()(name)

    return _ExecutorDecoratorCallable(
        name=name,
        config_field=resolve_config_field(config_field, config, '@system_storage'),
        required_resource_keys=required_resource_keys,
    )


class _ExecutorDecoratorCallable(object):
    def __init__(self, name=None, config_field=None, required_resource_keys=None):
        self.name = check.opt_str_param(name, 'name')
        self.config_field = config_field  # type check in definition
        self.required_resource_keys = required_resource_keys  # type check in definition

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        executor_def = ExecutorDefinition(
            name=self.name,
            config_field=self.config_field,
            executor_creation_fn=fn,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(executor_def, wrapped=fn)

        return executor_def


@executor(name='in_process')
def in_process_executor(init_context):
    '''The default in-process executor.

    In most Dagster environments, this will be the default executor. It is available by default on
    any :py:class:`ModeDefinition` that does not provide custom executors. To select it explicitly,
    include the following top-level fragment in config:

    .. code-block:: yaml

        execution:
          in_process:

    '''
    from dagster.core.engine.init import InitExecutorContext

    check.inst_param(init_context, 'init_context', InitExecutorContext)

    return InProcessExecutorConfig()


@executor(
    name='multiprocess', config={'max_concurrent': Field(Int, is_optional=True, default_value=0)}
)
def multiprocess_executor(init_context):
    '''The default multiprocess executor.

    This simple multiprocess executor is available by default on any :py:class:`ModeDefinition`
    that does not provide custom executors. To select the multiprocess executor, include a fragment
    such as the following in your config:

    .. code-block:: yaml

        execution:
          multiprocess:
            max_concurrent: 4
    
    The ``max_concurrent`` arg is optional and tells the execution engine how many processes may run
    concurrently. By default, or if you set ``max_concurrent`` to be 0, this is the return value of
    :py:func:`python:multiprocessing.cpu_count`.

    '''
    from dagster.core.definitions.handle import ExecutionTargetHandle
    from dagster.core.engine.init import InitExecutorContext

    check.inst_param(init_context, 'init_context', InitExecutorContext)

    handle, _ = ExecutionTargetHandle.get_handle(init_context.pipeline_def)
    return MultiprocessExecutorConfig(
        handle=handle, max_concurrent=init_context.executor_config['max_concurrent']
    )


default_executors = [in_process_executor, multiprocess_executor]
