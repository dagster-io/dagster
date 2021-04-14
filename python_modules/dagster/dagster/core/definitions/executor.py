from enum import Enum
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
from dagster.core.execution.retries import RetryMode, get_retries_config

from .definition_config_schema import convert_user_facing_definition_config_schema


class ExecutorRequirement(Enum):
    """
    An ExecutorDefinition can include a list of requirements that the system uses to
    check whether the executor will be able to work for a particular pipeline execution.
    """

    # The passed in IPipeline must be reconstructable across process boundaries
    RECONSTRUCTABLE_PIPELINE = "RECONSTRUCTABLE_PIPELINE"

    # The DagsterInstance must be loadable in a different process
    NON_EPHEMERAL_INSTANCE = "NON_EPHEMERAL_INSTANCE"

    # Any solid outputs on the pipeline must be persisted
    PERSISTENT_OUTPUTS = "PERSISTENT_OUTPUTS"


def multiple_process_executor_requirements():
    return [
        ExecutorRequirement.RECONSTRUCTABLE_PIPELINE,
        ExecutorRequirement.NON_EPHEMERAL_INSTANCE,
        ExecutorRequirement.PERSISTENT_OUTPUTS,
    ]


class ExecutorDefinition(NamedConfigurableDefinition):
    """
    Args:
        name (str): The name of the executor.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data
            available in `init_context.executor_config`. If not set, Dagster will accept any config
            provided.
        requirements (Optional[List[ExecutorRequirement]]): Any requirements that must
            be met in order for the executor to be usable for a particular pipeline execution.
        executor_creation_fn(Optional[Callable]): Should accept an :py:class:`InitExecutorContext`
            and return an instance of :py:class:`Executor`
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            executor.
    """

    def __init__(
        self,
        name,
        config_schema=None,
        requirements=None,
        executor_creation_fn=None,
        description=None,
    ):
        self._name = check.str_param(name, "name")
        self._requirements = check.opt_list_param(
            requirements, "requirements", of_type=ExecutorRequirement
        )
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
    def requirements(self):
        return self._requirements

    @property
    def executor_creation_fn(self):
        return self._executor_creation_fn

    def copy_for_configured(self, name, description, config_schema, _):
        return ExecutorDefinition(
            name=name,
            config_schema=config_schema,
            executor_creation_fn=self.executor_creation_fn,
            description=description or self.description,
            requirements=self.requirements,
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
            config_schema (Optional[ConfigSchema]): If config_or_config_fn is a function, the config
                schema that its input must satisfy. If not set, Dagster will accept any config
                provided.
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


def executor(
    name=None,
    config_schema=None,
    requirements=None,
):
    """Define an executor.

    The decorated function should accept an :py:class:`InitExecutorContext` and return an instance
    of :py:class:`Executor`.

    Args:
        name (Optional[str]): The name of the executor.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.executor_config`. If not set, Dagster will accept any config provided for.
        requirements (Optional[List[ExecutorRequirement]]): Any requirements that must
            be met in order for the executor to be usable for a particular pipeline execution.
    """
    if callable(name):
        check.invariant(config_schema is None)
        check.invariant(requirements is None)
        return _ExecutorDecoratorCallable()(name)

    return _ExecutorDecoratorCallable(
        name=name, config_schema=config_schema, requirements=requirements
    )


class _ExecutorDecoratorCallable:
    def __init__(self, name=None, config_schema=None, requirements=None):
        self.name = check.opt_str_param(name, "name")
        self.config_schema = config_schema  # type check in definition
        self.requirements = requirements

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        executor_def = ExecutorDefinition(
            name=self.name,
            config_schema=self.config_schema,
            executor_creation_fn=fn,
            requirements=self.requirements,
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
        retries=RetryMode.from_config(init_context.executor_config.get("retries", {"enabled": {}})),
        marker_to_close=init_context.executor_config.get("marker_to_close"),
    )


@executor(
    name="multiprocess",
    config_schema={
        "max_concurrent": Field(Int, is_required=False, default_value=0),
        "retries": get_retries_config(),
    },
    requirements=multiple_process_executor_requirements(),
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

    return MultiprocessExecutor(
        max_concurrent=init_context.executor_config["max_concurrent"],
        retries=RetryMode.from_config(init_context.executor_config["retries"]),
    )


default_executors = [in_process_executor, multiprocess_executor]


def check_cross_process_constraints(init_context):
    from dagster.core.executor.init import InitExecutorContext

    check.inst_param(init_context, "init_context", InitExecutorContext)

    if ExecutorRequirement.RECONSTRUCTABLE_PIPELINE in init_context.executor_def.requirements:
        _check_intra_process_pipeline(init_context.pipeline)

    if ExecutorRequirement.NON_EPHEMERAL_INSTANCE in init_context.executor_def.requirements:
        _check_non_ephemeral_instance(init_context.instance)


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


def _check_non_ephemeral_instance(instance):
    if instance.is_ephemeral:
        raise DagsterUnmetExecutorRequirementsError(
            "You have attempted to use an executor that uses multiple processes with an "
            "ephemeral DagsterInstance. A non-ephemeral instance is needed to coordinate "
            "execution between multiple processes. You can configure your default instance "
            "via $DAGSTER_HOME or ensure a valid one is passed when invoking the python APIs."
        )
