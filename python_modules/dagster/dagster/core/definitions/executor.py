from functools import update_wrapper

from dagster import check
from dagster.builtins import Int
from dagster.config.field import Field
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.execution.config import InProcessExecutorConfig, MultiprocessExecutorConfig
from dagster.core.execution.retries import Retries, get_retries_config


class ExecutorDefinition(object):
    '''
    Args:
        name (Optional[str]): The name of the executor.
        config (Optional[Any]): The schema for the config. Configuration data available in
            `init_context.executor_config`.

            This value can be any of:

            1. A Python primitive type that resolves to a Dagster config type 
               (:py:class:`~python:int`, :py:class:`~python:float`, :py:class:`~python:bool`,
               :py:class:`~python:str`, or :py:class:`~python:list`).

            2. A Dagster config type: :py:data:`~dagster.Int`, :py:data:`~dagster.Float`,
               :py:data:`~dagster.Bool`, :py:data:`~dagster.String`,
               :py:data:`~dagster.StringSource`, :py:data:`~dagster.Path`, :py:data:`~dagster.Any`,
               :py:class:`~dagster.Array`, :py:data:`~dagster.Noneable`, :py:data:`~dagster.Enum`,
               :py:class:`~dagster.Selector`, :py:class:`~dagster.Shape`, or
               :py:class:`~dagster.Permissive`.

            3. A bare python dictionary, which will be automatically wrapped in
               :py:class:`~dagster.Shape`. Values of the dictionary are resolved recursively
               according to the same rules.

            4. A bare python list of length one which itself is config type.
               Becomes :py:class:`Array` with list element as an argument.

            5. An instance of :py:class:`~dagster.Field`.

        executor_creation_fn(Optional[Callable]): Should accept an :py:class:`InitExecutorContext`
            and return an instance of :py:class:`ExecutorConfig`.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            executor.

    '''

    def __init__(self, name, config=None, executor_creation_fn=None, required_resource_keys=None):
        self._name = check.str_param(name, 'name')
        self._config_field = check_user_facing_opt_config_param(config, 'config')
        self._executor_creation_fn = check.opt_callable_param(
            executor_creation_fn, 'executor_creation_fn'
        )
        self._required_resource_keys = frozenset(
            check.opt_set_param(required_resource_keys, 'required_resource_keys', of_type=str)
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


def executor(name=None, config=None, required_resource_keys=None):
    '''Define an executor.

    The decorated function should accept an :py:class:`InitExecutorContext` and return an instance
    of :py:class:`ExecutorConfig`.

    Args:
        name (Optional[str]): The name of the executor.
        config (Optional[Any]): The schema for the config. Configuration data available in
            `init_context.executor_config`.

            This value can be any of:

            1. A Python primitive type that resolves to a Dagster config type 
               (:py:class:`~python:int`, :py:class:`~python:float`, :py:class:`~python:bool`,
               :py:class:`~python:str`, or :py:class:`~python:list`).

            2. A Dagster config type: :py:data:`~dagster.Int`, :py:data:`~dagster.Float`,
               :py:data:`~dagster.Bool`, :py:data:`~dagster.String`,
               :py:data:`~dagster.StringSource`, :py:data:`~dagster.Path`, :py:data:`~dagster.Any`,
               :py:class:`~dagster.Array`, :py:data:`~dagster.Noneable`, :py:data:`~dagster.Enum`,
               :py:class:`~dagster.Selector`, :py:class:`~dagster.Shape`, or
               :py:class:`~dagster.Permissive`.

            3. A bare python dictionary, which will be automatically wrapped in
               :py:class:`~dagster.Shape`. Values of the dictionary are resolved recursively
               according to the same rules.

            4. A bare python list of length one which itself is config type.
               Becomes :py:class:`Array` with list element as an argument.

            5. An instance of :py:class:`~dagster.Field`.

        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            executor.
    '''
    if callable(name):
        check.invariant(config is None)
        check.invariant(required_resource_keys is None)
        return _ExecutorDecoratorCallable()(name)

    return _ExecutorDecoratorCallable(
        name=name, config=config, required_resource_keys=required_resource_keys,
    )


class _ExecutorDecoratorCallable(object):
    def __init__(self, name=None, config=None, required_resource_keys=None):
        self.name = check.opt_str_param(name, 'name')
        self.config = config  # type check in definition
        self.required_resource_keys = required_resource_keys  # type check in definition

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        executor_def = ExecutorDefinition(
            name=self.name,
            config=self.config,
            executor_creation_fn=fn,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(executor_def, wrapped=fn)

        return executor_def


@executor(
    name='in_process',
    config={'retries': get_retries_config(), 'marker_to_close': Field(str, is_required=False),},
)
def in_process_executor(init_context):
    '''The default in-process executor.

    In most Dagster environments, this will be the default executor. It is available by default on
    any :py:class:`ModeDefinition` that does not provide custom executors. To select it explicitly,
    include the following top-level fragment in config:

    .. code-block:: yaml

        execution:
          in_process:

    Execution priority can be configured using the ``dagster/priority`` tag via solid metadata,
    where the higher the number the higher the priority. 0 is the default and both positive
    and negative numbers can be used.
    '''
    from dagster.core.engine.init import InitExecutorContext

    check.inst_param(init_context, 'init_context', InitExecutorContext)

    return InProcessExecutorConfig(
        # shouldn't need to .get() here - issue with defaults in config setup
        retries=Retries.from_config(init_context.executor_config.get('retries', {'enabled': {}})),
        marker_to_close=init_context.executor_config.get('marker_to_close'),
    )


@executor(
    name='multiprocess',
    config={
        'max_concurrent': Field(Int, is_required=False, default_value=0),
        'retries': get_retries_config(),
    },
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

    Execution priority can be configured using the ``dagster/priority`` tag via solid metadata,
    where the higher the number the higher the priority. 0 is the default and both positive
    and negative numbers can be used.
    '''
    from dagster.core.definitions.handle import ExecutionTargetHandle
    from dagster.core.engine.init import InitExecutorContext

    check.inst_param(init_context, 'init_context', InitExecutorContext)

    check_cross_process_constraints(init_context)

    handle, _ = ExecutionTargetHandle.get_handle(init_context.pipeline_def)
    return MultiprocessExecutorConfig(
        handle=handle,
        max_concurrent=init_context.executor_config['max_concurrent'],
        retries=Retries.from_config(init_context.executor_config['retries']),
    )


default_executors = [in_process_executor, multiprocess_executor]


def check_cross_process_constraints(init_context):
    from dagster.core.engine.init import InitExecutorContext

    check.inst_param(init_context, 'init_context', InitExecutorContext)

    _check_pipeline_has_target_handle(init_context.pipeline_def)
    _check_non_ephemeral_instance(init_context.instance)
    _check_persistent_storage_requirement(init_context.system_storage_def)


def _check_pipeline_has_target_handle(pipeline_def):
    from dagster.core.definitions.handle import ExecutionTargetHandle

    handle, _ = ExecutionTargetHandle.get_handle(pipeline_def)
    if not handle:
        raise DagsterUnmetExecutorRequirementsError(
            'You have attempted to use an executor that uses multiple processes with the pipeline "{name}" '
            'that can not be re-hydrated. Pipelines must be loaded in a way that allows dagster to reconstruct '
            'them in a new process. This means: \n'
            '  * using the file, module, or repository.yaml arguments of dagit/dagster-graphql/dagster\n'
            '  * constructing an ExecutionTargetHandle directly\n'.format(name=pipeline_def.name)
        )


def _check_persistent_storage_requirement(system_storage_def):
    if not system_storage_def.is_persistent:
        raise DagsterUnmetExecutorRequirementsError(
            (
                'You have attempted to use an executor that uses multiple processes while using system '
                'storage {storage_name} which does not persist intermediates. '
                'This means there would be no way to move data between different '
                'processes. Please configure your pipeline in the storage config '
                'section to use persistent system storage such as the filesystem.'
            ).format(storage_name=system_storage_def.name)
        )


def _check_non_ephemeral_instance(instance):
    if instance.is_ephemeral:
        raise DagsterUnmetExecutorRequirementsError(
            'You have attempted to use an executor that uses multiple processes with an '
            'ephemeral DagsterInstance. A non-ephemeral instance is needed to coordinate '
            'execution between multiple processes. You can configure your default instance '
            'via $DAGSTER_HOME or ensure a valid one is passed when invoking the python APIs.'
        )
