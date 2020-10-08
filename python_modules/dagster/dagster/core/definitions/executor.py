from functools import update_wrapper

from dagster import check
from dagster.builtins import Int
from dagster.config.field import Field
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.core.definitions.config_mappable import IConfigMappable
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.execution.retries import Retries, get_retries_config
from dagster.utils.backcompat import rename_warning


class ExecutorDefinition(IConfigMappable):
    """
    Args:
        name (Optional[str]): The name of the executor.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data
            available in `init_context.executor_config`.
        executor_creation_fn(Optional[Callable]): Should accept an :py:class:`InitExecutorContext`
            and return an instance of :py:class:`Executor`
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            executor.
        _configured_config_mapping_fn: This argument is for internal use only. Users should not
            specify this field. To preconfigure a resource, use the :py:func:`configured` API.
    """

    def __init__(
        self,
        name,
        config_schema=None,
        executor_creation_fn=None,
        required_resource_keys=None,
        _configured_config_mapping_fn=None,
    ):
        self._name = check.str_param(name, "name")
        self._config_schema = check_user_facing_opt_config_param(config_schema, "config_schema")
        self._executor_creation_fn = check.opt_callable_param(
            executor_creation_fn, "executor_creation_fn"
        )
        self._required_resource_keys = frozenset(
            check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
        )
        self.__configured_config_mapping_fn = check.opt_callable_param(
            _configured_config_mapping_fn, "config_mapping_fn"
        )

    @property
    def name(self):
        return self._name

    @property
    def config_field(self):
        rename_warning("config_schema", "config_field", "0.9.0")
        return self._config_schema

    @property
    def config_schema(self):
        return self._config_schema

    @property
    def executor_creation_fn(self):
        return self._executor_creation_fn

    @property
    def required_resource_keys(self):
        return self._required_resource_keys

    @property
    def _configured_config_mapping_fn(self):
        return self.__configured_config_mapping_fn

    def configured(self, config_or_config_fn, config_schema=None, **kwargs):
        wrapped_config_mapping_fn = self._get_wrapped_config_mapping_fn(
            config_or_config_fn, config_schema
        )

        return ExecutorDefinition(
            config_schema=config_schema,
            name=kwargs.get("name", self.name),
            executor_creation_fn=self.executor_creation_fn,
            required_resource_keys=self.required_resource_keys,
            _configured_config_mapping_fn=wrapped_config_mapping_fn,
        )


def executor(name=None, config_schema=None, required_resource_keys=None):
    """Define an executor.

    The decorated function should accept an :py:class:`InitExecutorContext` and return an instance
    of :py:class:`Executor`.

    Args:
        name (Optional[str]): The name of the executor.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.executor_config`.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            executor.
    """
    if callable(name):
        check.invariant(config_schema is None)
        check.invariant(required_resource_keys is None)
        return _ExecutorDecoratorCallable()(name)

    return _ExecutorDecoratorCallable(
        name=name, config_schema=config_schema, required_resource_keys=required_resource_keys,
    )


class _ExecutorDecoratorCallable(object):
    def __init__(self, name=None, config_schema=None, required_resource_keys=None):
        self.name = check.opt_str_param(name, "name")
        self.config_schema = config_schema  # type check in definition
        self.required_resource_keys = required_resource_keys  # type check in definition

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        executor_def = ExecutorDefinition(
            name=self.name,
            config_schema=self.config_schema,
            executor_creation_fn=fn,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(executor_def, wrapped=fn)

        return executor_def


@executor(
    name="in_process",
    config_schema={
        "retries": get_retries_config(),
        "marker_to_close": Field(str, is_required=False),
    },
)
def in_process_executor(init_context):
    """The default in-process executor.

    In most Dagster environments, this will be the default executor. It is available by default on
    any :py:class:`ModeDefinition` that does not provide custom executors. To select it explicitly,
    include the following top-level fragment in config:

    .. code-block:: yaml

        execution:
          in_process:

    Execution priority can be configured using the ``dagster/priority`` tag via solid metadata,
    where the higher the number the higher the priority. 0 is the default and both positive
    and negative numbers can be used.
    """
    from dagster.core.executor.init import InitExecutorContext
    from dagster.core.executor.in_process import InProcessExecutor

    check.inst_param(init_context, "init_context", InitExecutorContext)

    return InProcessExecutor(
        # shouldn't need to .get() here - issue with defaults in config setup
        retries=Retries.from_config(init_context.executor_config.get("retries", {"enabled": {}})),
        marker_to_close=init_context.executor_config.get("marker_to_close"),
    )


@executor(
    name="multiprocess",
    config_schema={
        "max_concurrent": Field(Int, is_required=False, default_value=0),
        "retries": get_retries_config(),
    },
)
def multiprocess_executor(init_context):
    """The default multiprocess executor.

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
    """
    from dagster.core.executor.init import InitExecutorContext
    from dagster.core.executor.multiprocess import MultiprocessExecutor

    check.inst_param(init_context, "init_context", InitExecutorContext)

    check_cross_process_constraints(init_context)

    return MultiprocessExecutor(
        pipeline=init_context.pipeline,
        max_concurrent=init_context.executor_config["max_concurrent"],
        retries=Retries.from_config(init_context.executor_config["retries"]),
    )


default_executors = [in_process_executor, multiprocess_executor]


def check_cross_process_constraints(init_context):
    from dagster.core.executor.init import InitExecutorContext

    check.inst_param(init_context, "init_context", InitExecutorContext)

    _check_intra_process_pipeline(init_context.pipeline)
    _check_non_ephemeral_instance(init_context.instance)
    _check_persistent_storage_requirement(
        init_context.intermediate_storage_def, init_context.system_storage_def
    )


def _check_intra_process_pipeline(pipeline):
    if not isinstance(pipeline, ReconstructablePipeline):
        raise DagsterUnmetExecutorRequirementsError(
            'You have attempted to use an executor that uses multiple processes with the pipeline "{name}" '
            "that is not reconstructable. Pipelines must be loaded in a way that allows dagster to reconstruct "
            "them in a new process. This means: \n"
            "  * using the file, module, or repository.yaml arguments of dagit/dagster-graphql/dagster\n"
            "  * loading the pipeline through the reconstructable() function\n".format(
                name=pipeline.get_definition().name
            )
        )


def _check_persistent_storage_requirement(intermediate_storage_def, system_storage_def):
    if intermediate_storage_def:
        if not intermediate_storage_def.is_persistent:
            raise DagsterUnmetExecutorRequirementsError(
                (
                    "You have attempted to use an executor that uses multiple processes while using "
                    "intermediate storage {storage_name} which does not persist intermediates. "
                    "This means there would be no way to move data between different "
                    "processes. Please configure your pipeline in the storage config "
                    "section to use persistent system storage such as the filesystem."
                ).format(storage_name=intermediate_storage_def.name)
            )
    elif not system_storage_def.is_persistent:
        raise DagsterUnmetExecutorRequirementsError(
            (
                "You have attempted to use an executor that uses multiple processes while using system "
                "storage {storage_name} which does not persist intermediates. "
                "This means there would be no way to move data between different "
                "processes. Please configure your pipeline in the storage config "
                "section to use persistent system storage such as the filesystem."
            ).format(storage_name=system_storage_def.name)
        )


def _check_non_ephemeral_instance(instance):
    if instance.is_ephemeral:
        raise DagsterUnmetExecutorRequirementsError(
            "You have attempted to use an executor that uses multiple processes with an "
            "ephemeral DagsterInstance. A non-ephemeral instance is needed to coordinate "
            "execution between multiple processes. You can configure your default instance "
            "via $DAGSTER_HOME or ensure a valid one is passed when invoking the python APIs."
        )
