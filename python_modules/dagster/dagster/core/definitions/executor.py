from functools import update_wrapper
from typing import Any, Dict, Optional

from dagster import check
from dagster.builtins import Int
from dagster.config.field import Field
from dagster.core.definitions.configurable import (
    ConfiguredDefinitionConfigSchema,
    NamedConfigurableDefinition,
)
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.execution.retries import Retries, get_retries_config

from .definition_config_schema import convert_user_facing_definition_config_schema


class ExecutorDefinition(NamedConfigurableDefinition):
    """
    Args:
        name (str): The name of the executor.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data
            available in `init_context.executor_config`.
        executor_creation_fn(Optional[Callable]): Should accept an :py:class:`InitExecutorContext`
            and return an instance of :py:class:`Executor`
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            executor.
    """

    def __init__(
        self, name, config_schema=None, executor_creation_fn=None, description=None,
    ):
        self._name = check.str_param(name, "name")
        self._config_schema = convert_user_facing_definition_config_schema(config_schema)
        self._executor_creation_fn = check.opt_callable_param(
            executor_creation_fn, "executor_creation_fn"
        )
        self._description = check.opt_str_param(description, "description")

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def config_schema(self):
        return self._config_schema

    @property
    def executor_creation_fn(self):
        return self._executor_creation_fn

    def copy_for_configured(self, name, description, config_schema, _):
        return ExecutorDefinition(
            name=name,
            config_schema=config_schema,
            executor_creation_fn=self.executor_creation_fn,
            description=description or self.description,
        )

    # Backcompat: Overrides configured method to provide name as a keyword argument.
    # If no name is provided, the name is pulled off of this ExecutorDefinition.
    def configured(
        self,
        config_or_config_fn: Any,
        name: Optional[str] = None,
        config_schema: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ):
        """
        Wraps this object in an object of the same type that provides configuration to the inner
        object.

        Args:
            config_or_config_fn (Union[Any, Callable[[Any], Any]]): Either (1) Run configuration
                that fully satisfies this object's config schema or (2) A function that accepts run
                configuration and returns run configuration that fully satisfies this object's
                config schema.  In the latter case, config_schema must be specified.  When
                passing a function, it's easiest to use :py:func:`configured`.
            name (Optional[str]): Name of the new definition. If not provided, the emitted
                definition will inherit the name of the `ExecutorDefinition` upon which this
                function is called.
            config_schema (ConfigSchema): If config_or_config_fn is a function, the config schema
                that its input must satisfy.
            description (Optional[str]): Description of the new definition. If not specified,
                inherits the description of the definition being configured.

        Returns (ConfigurableDefinition): A configured version of this object.
        """

        name = check.opt_str_param(name, "name")

        new_config_schema = ConfiguredDefinitionConfigSchema(
            self, convert_user_facing_definition_config_schema(config_schema), config_or_config_fn
        )

        return self.copy_for_configured(
            name or self.name, description, new_config_schema, config_or_config_fn
        )


def executor(name=None, config_schema=None):
    """Define an executor.

    The decorated function should accept an :py:class:`InitExecutorContext` and return an instance
    of :py:class:`Executor`.

    Args:
        name (Optional[str]): The name of the executor.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.executor_config`.
    """
    if callable(name):
        check.invariant(config_schema is None)
        return _ExecutorDecoratorCallable()(name)

    return _ExecutorDecoratorCallable(name=name, config_schema=config_schema)


class _ExecutorDecoratorCallable:
    def __init__(self, name=None, config_schema=None):
        self.name = check.opt_str_param(name, "name")
        self.config_schema = config_schema  # type check in definition

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        executor_def = ExecutorDefinition(
            name=self.name, config_schema=self.config_schema, executor_creation_fn=fn,
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
            config:
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
        init_context.pipeline.get_definition(),
        init_context.mode_def,
        init_context.intermediate_storage_def,
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


def _all_outputs_non_mem_io_managers(pipeline_def, mode_def):
    """Returns true if every output definition in the pipeline uses an IO manager that's not
    the mem_io_manager.

    If true, this indicates that it's OK to execute steps in their own processes, because their
    outputs will be available to other processes.
    """
    # pylint: disable=comparison-with-callable
    from dagster.core.storage.mem_io_manager import mem_io_manager

    output_defs = [
        output_def
        for solid_def in pipeline_def.all_solid_defs
        for output_def in solid_def.output_defs
    ]
    for output_def in output_defs:
        if mode_def.resource_defs[output_def.io_manager_key] == mem_io_manager:
            return False

    return True


def _check_persistent_storage_requirement(pipeline_def, mode_def, intermediate_storage_def):
    """We prefer to store outputs with IO managers, but will fall back to intermediate storage
    if an IO manager isn't set.
    """
    if not (
        _all_outputs_non_mem_io_managers(pipeline_def, mode_def)
        or (intermediate_storage_def and intermediate_storage_def.is_persistent)
    ):
        raise DagsterUnmetExecutorRequirementsError(
            "You have attempted to use an executor that uses multiple processes, but your pipeline "
            "includes solid outputs that will not be stored somewhere where other processes can"
            "retrieve them. "
            "Please make sure that your pipeline definition includes a ModeDefinition whose "
            'resource_keys assign the "io_manager" key to an IOManager resource '
            "that stores outputs outside of the process, such as the fs_io_manager."
        )


def _check_non_ephemeral_instance(instance):
    if instance.is_ephemeral:
        raise DagsterUnmetExecutorRequirementsError(
            "You have attempted to use an executor that uses multiple processes with an "
            "ephemeral DagsterInstance. A non-ephemeral instance is needed to coordinate "
            "execution between multiple processes. You can configure your default instance "
            "via $DAGSTER_HOME or ensure a valid one is passed when invoking the python APIs."
        )
