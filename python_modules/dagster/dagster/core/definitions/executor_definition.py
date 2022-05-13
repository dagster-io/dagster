from enum import Enum as PyEnum
from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union, overload

from typing_extensions import TypeAlias

import dagster._check as check
from dagster.builtins import Int
from dagster.config import Field, Selector
from dagster.config.config_schema import ConfigSchemaType
from dagster.core.definitions.configurable import (
    ConfiguredDefinitionConfigSchema,
    NamedConfigurableDefinition,
)
from dagster.core.definitions.pipeline_base import IPipeline
from dagster.core.definitions.reconstruct import ReconstructablePipeline
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.execution.retries import RetryMode, get_retries_config

from .definition_config_schema import (
    IDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)

if TYPE_CHECKING:
    from dagster.core.executor.base import Executor
    from dagster.core.executor.in_process import InProcessExecutor
    from dagster.core.executor.init import InitExecutorContext
    from dagster.core.executor.multiprocess import MultiprocessExecutor
    from dagster.core.instance import DagsterInstance


class ExecutorRequirement(PyEnum):
    """
    An ExecutorDefinition can include a list of requirements that the system uses to
    check whether the executor will be able to work for a particular job/pipeline execution.
    """

    # The passed in IPipeline must be reconstructable across process boundaries
    RECONSTRUCTABLE_PIPELINE = "RECONSTRUCTABLE_PIPELINE"  # This needs to still exist for folks who may have written their own executor
    RECONSTRUCTABLE_JOB = "RECONSTRUCTABLE_PIPELINE"

    # The DagsterInstance must be loadable in a different process
    NON_EPHEMERAL_INSTANCE = "NON_EPHEMERAL_INSTANCE"

    # Any solid outputs on the pipeline must be persisted
    PERSISTENT_OUTPUTS = "PERSISTENT_OUTPUTS"


def multiple_process_executor_requirements() -> List[ExecutorRequirement]:
    return [
        ExecutorRequirement.RECONSTRUCTABLE_JOB,
        ExecutorRequirement.NON_EPHEMERAL_INSTANCE,
        ExecutorRequirement.PERSISTENT_OUTPUTS,
    ]


ExecutorConfig = Dict[str, object]
ExecutorCreationFunction: TypeAlias = Callable[["InitExecutorContext"], "Executor"]
ExecutorRequirementsFunction: TypeAlias = Callable[[ExecutorConfig], List[ExecutorRequirement]]


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
        name: str,
        config_schema: Optional[ConfigSchemaType] = None,
        requirements: Union[
            ExecutorRequirementsFunction, Optional[List[ExecutorRequirement]]
        ] = None,
        executor_creation_fn: Optional[ExecutorCreationFunction] = None,
        description: Optional[str] = None,
    ):
        self._name = check.str_param(name, "name")
        self._requirements_fn: ExecutorRequirementsFunction
        if callable(requirements):
            self._requirements_fn = requirements
        else:
            requirements_lst = check.opt_list_param(
                requirements, "requirements", of_type=ExecutorRequirement
            )
            self._requirements_fn = lambda _: requirements_lst
        self._config_schema = convert_user_facing_definition_config_schema(config_schema)
        self._executor_creation_fn = check.opt_callable_param(
            executor_creation_fn, "executor_creation_fn"
        )
        self._description = check.opt_str_param(description, "description")

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def config_schema(self) -> IDefinitionConfigSchema:
        return self._config_schema

    def get_requirements(self, executor_config: Dict[str, object]) -> List[ExecutorRequirement]:
        return self._requirements_fn(executor_config)

    @property
    def executor_creation_fn(self) -> Optional[ExecutorCreationFunction]:
        return self._executor_creation_fn

    def copy_for_configured(self, name, description, config_schema, _) -> "ExecutorDefinition":
        return ExecutorDefinition(
            name=name,
            config_schema=config_schema,
            executor_creation_fn=self.executor_creation_fn,
            description=description or self.description,
            requirements=self._requirements_fn,
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


@overload
def executor(name: ExecutorCreationFunction) -> ExecutorDefinition:
    ...


@overload
def executor(
    name: Optional[str] = ...,
    config_schema: Optional[ConfigSchemaType] = ...,
    requirements: Optional[Union[ExecutorRequirementsFunction, List[ExecutorRequirement]]] = ...,
) -> "_ExecutorDecoratorCallable":
    ...


def executor(
    name: Union[ExecutorCreationFunction, Optional[str]] = None,
    config_schema: Optional[ConfigSchemaType] = None,
    requirements: Optional[Union[ExecutorRequirementsFunction, List[ExecutorRequirement]]] = None,
) -> Union[ExecutorDefinition, "_ExecutorDecoratorCallable"]:
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

    def __call__(self, fn: ExecutorCreationFunction) -> ExecutorDefinition:
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


def _core_in_process_executor_creation(config: ExecutorConfig) -> "InProcessExecutor":
    from dagster.core.executor.in_process import InProcessExecutor

    return InProcessExecutor(
        # shouldn't need to .get() here - issue with defaults in config setup
        retries=RetryMode.from_config(check.dict_elem(config, "retries")),
        marker_to_close=config.get("marker_to_close"),
    )


IN_PROC_CONFIG = {
    "retries": get_retries_config(),
    "marker_to_close": Field(str, is_required=False),
}


@executor(
    name="in_process",
    config_schema=IN_PROC_CONFIG,
)
def in_process_executor(init_context):
    """The in-process executor executes all steps in a single process.

    For legacy pipelines, this will be the default executor. To select it explicitly,
    include the following top-level fragment in config:

    .. code-block:: yaml

        execution:
          in_process:

    Execution priority can be configured using the ``dagster/priority`` tag via solid/op metadata,
    where the higher the number the higher the priority. 0 is the default and both positive
    and negative numbers can be used.
    """
    return _core_in_process_executor_creation(init_context.executor_config)


@executor(name="execute_in_process_executor")
def execute_in_process_executor(_) -> "InProcessExecutor":
    """Executor used by execute_in_process.

    Use of this executor triggers special behavior in the config system that ignores all incoming
    executor config. This is because someone might set executor config on a job, and when we foist
    this executor onto the job for `execute_in_process`, that config becomes nonsensical.
    """
    from dagster.core.executor.in_process import InProcessExecutor

    return InProcessExecutor(
        retries=RetryMode.ENABLED,
        marker_to_close=None,
    )


def _core_multiprocess_executor_creation(config: ExecutorConfig) -> "MultiprocessExecutor":
    from dagster.core.executor.multiprocess import MultiprocessExecutor

    # unpack optional selector
    start_method = None
    start_cfg: Dict[str, object] = {}
    start_selector = check.opt_dict_elem(config, "start_method")
    if start_selector:
        start_method, start_cfg = list(start_selector.items())[0]

    return MultiprocessExecutor(
        max_concurrent=check.int_elem(config, "max_concurrent"),
        retries=RetryMode.from_config(check.dict_elem(config, "retries")),  # type: ignore
        start_method=start_method,
        explicit_forkserver_preload=check.opt_list_elem(start_cfg, "preload_modules", of_type=str),
    )


MULTI_PROC_CONFIG = {
    "max_concurrent": Field(Int, is_required=False, default_value=0),
    "start_method": Field(
        Selector(
            {
                "spawn": {},
                "forkserver": {
                    "preload_modules": Field(
                        [str],
                        is_required=False,
                        description="Explicit modules to preload in the forkserver.",
                    ),
                },
                # fork currently unsupported due to threads usage
            }
        ),
        is_required=False,
        description=(
            "Select how subprocesses are created. Defaults to spawn.\n"
            "When forkserver is selected, set_forkserver_preload will be called with either:\n"
            "* the preload_modules list if provided by config\n"
            "* the module containing the Job if it was loaded from a module\n"
            "* dagster\n"
            "https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods"
        ),
    ),
    "retries": get_retries_config(),
}


@executor(
    name="multiprocess",
    config_schema=MULTI_PROC_CONFIG,
    requirements=multiple_process_executor_requirements(),
)
def multiprocess_executor(init_context):
    """The multiprocess executor executes each step in an individual process.

    Any job that does not specify custom executors will use the multiprocess_executor by default.
    For jobs or legacy pipelines, to configure the multiprocess executor, include a fragment such
    as the following in your run config:

    .. code-block:: yaml

        execution:
          config:
            multiprocess:
              max_concurrent: 4

    The ``max_concurrent`` arg is optional and tells the execution engine how many processes may run
    concurrently. By default, or if you set ``max_concurrent`` to be 0, this is the return value of
    :py:func:`python:multiprocessing.cpu_count`.

    Execution priority can be configured using the ``dagster/priority`` tag via solid/op metadata,
    where the higher the number the higher the priority. 0 is the default and both positive
    and negative numbers can be used.
    """
    return _core_multiprocess_executor_creation(init_context.executor_config)


default_executors = [in_process_executor, multiprocess_executor]


def check_cross_process_constraints(init_context: "InitExecutorContext") -> None:
    from dagster.core.executor.init import InitExecutorContext

    check.inst_param(init_context, "init_context", InitExecutorContext)
    requirements_lst = init_context.executor_def.get_requirements(init_context.executor_config)

    if ExecutorRequirement.RECONSTRUCTABLE_JOB in requirements_lst:
        _check_intra_process_pipeline(init_context.pipeline)

    if ExecutorRequirement.NON_EPHEMERAL_INSTANCE in requirements_lst:
        _check_non_ephemeral_instance(init_context.instance)


def _check_intra_process_pipeline(pipeline: IPipeline) -> None:
    from dagster.core.definitions import JobDefinition

    if not isinstance(pipeline, ReconstructablePipeline):
        target = "job" if isinstance(pipeline.get_definition(), JobDefinition) else "pipeline"
        raise DagsterUnmetExecutorRequirementsError(
            'You have attempted to use an executor that uses multiple processes with the {target} "{name}" '
            "that is not reconstructable. {target_cap} must be loaded in a way that allows dagster to reconstruct "
            "them in a new process. This means: \n"
            "  * using the file, module, or repository.yaml arguments of dagit/dagster-graphql/dagster\n"
            "  * loading the {target} through the reconstructable() function\n".format(
                target=target, name=pipeline.get_definition().name, target_cap=target.capitalize()
            )
        )


def _check_non_ephemeral_instance(instance: "DagsterInstance") -> None:
    if instance.is_ephemeral:
        raise DagsterUnmetExecutorRequirementsError(
            "You have attempted to use an executor that uses multiple processes with an "
            "ephemeral DagsterInstance. A non-ephemeral instance is needed to coordinate "
            "execution between multiple processes. You can configure your default instance "
            "via $DAGSTER_HOME or ensure a valid one is passed when invoking the python APIs. "
            "You can learn more about setting up a persistent DagsterInstance from the "
            "DagsterInstance docs here: https://docs.dagster.io/deployment/dagster-instance#default-local-behavior"
        )


def _get_default_executor_requirements(
    executor_config: ExecutorConfig,
) -> List[ExecutorRequirement]:
    return multiple_process_executor_requirements() if "multiprocess" in executor_config else []


@executor(
    name="multi_or_in_process_executor",
    config_schema=Field(
        Selector(
            {"multiprocess": MULTI_PROC_CONFIG, "in_process": IN_PROC_CONFIG},
        ),
        default_value={"multiprocess": {}},
    ),
    requirements=_get_default_executor_requirements,
)
def multi_or_in_process_executor(init_context: "InitExecutorContext") -> "Executor":
    """The default executor for a job.

    This is the executor available by default on a :py:class:`JobDefinition`
    that does not provide custom executors. This executor has a multiprocessing-enabled mode, and a
    single-process mode. By default, multiprocessing mode is enabled. Switching between multiprocess
    mode and in-process mode can be achieved via config.

    .. code-block:: yaml

        execution:
          config:
            multiprocess:


        execution:
          config:
            in_process:

    When using the multiprocess mode, ``max_concurrent`` and ``retries`` can also be configured.


          multiprocess:
            config:
              max_concurrent: 4
              retries:
                enabled:

    The ``max_concurrent`` arg is optional and tells the execution engine how many processes may run
    concurrently. By default, or if you set ``max_concurrent`` to be 0, this is the return value of
    :py:func:`python:multiprocessing.cpu_count`.

    When using the in_process mode, then only retries can be configured.

    Execution priority can be configured using the ``dagster/priority`` tag via solid metadata,
    where the higher the number the higher the priority. 0 is the default and both positive
    and negative numbers can be used.
    """
    if "multiprocess" in init_context.executor_config:
        return _core_multiprocess_executor_creation(
            check.dict_elem(init_context.executor_config, "multiprocess")
        )
    else:
        return _core_in_process_executor_creation(
            check.dict_elem(init_context.executor_config, "in_process")
        )
