from typing import TYPE_CHECKING, Any, Dict, Optional, Union, cast

from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.op_definition import OpDefinition
from dagster.core.definitions.solid_definition import SolidDefinition
from dagster.core.errors import DagsterInvariantViolationError

if TYPE_CHECKING:
    from .output import OutputContext
    from dagster.core.definitions.resource_definition import Resources
    from dagster.core.log_manager import DagsterLogManager
    from dagster.core.types.dagster_type import DagsterType
    from dagster.core.execution.context.system import StepExecutionContext


class InputContext:
    """
    The ``context`` object available to the load_input method of :py:class:`RootInputManager`.

    Attributes:
        name (Optional[str]): The name of the input that we're loading.
        pipeline_name (Optional[str]): The name of the pipeline.
        solid_def (Optional[SolidDefinition]): The definition of the solid that's loading the input.
        config (Optional[Any]): The config attached to the input that we're loading.
        metadata (Optional[Dict[str, Any]]): A dict of metadata that is assigned to the
            InputDefinition that we're loading for.
        upstream_output (Optional[OutputContext]): Info about the output that produced the object
            we're loading.
        dagster_type (Optional[DagsterType]): The type of this input.
        log (Optional[DagsterLogManager]): The log manager to use for this input.
        resource_config (Optional[Dict[str, Any]]): The config associated with the resource that
            initializes the RootInputManager.
        resources (Optional[Resources]): The resources required by the resource that initializes the
            input manager. If using the :py:func:`@root_input_manager` decorator, these resources
            correspond to those requested with the `required_resource_keys` parameter.
        op_def (Optional[OpDefinition]): The definition of the op that's loading the input.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        solid_def: Optional["SolidDefinition"] = None,
        config: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        upstream_output: Optional["OutputContext"] = None,
        dagster_type: Optional["DagsterType"] = None,
        log_manager: Optional["DagsterLogManager"] = None,
        resource_config: Optional[Dict[str, Any]] = None,
        resources: Optional[Union["Resources", Dict[str, Any]]] = None,
        step_context: Optional["StepExecutionContext"] = None,
        op_def: Optional["OpDefinition"] = None,
    ):
        from dagster.core.definitions.resource_definition import Resources, IContainsGenerator
        from dagster.core.execution.build_resources import build_resources

        self._name = name
        self._pipeline_name = pipeline_name
        check.invariant(
            solid_def is None or op_def is None, "Can't provide both a solid_def and an op_def arg"
        )
        self._solid_def = solid_def or op_def
        self._config = config
        self._metadata = metadata
        self._upstream_output = upstream_output
        self._dagster_type = dagster_type
        self._log = log_manager
        self._resource_config = resource_config
        self._step_context = step_context

        if isinstance(resources, Resources):
            self._resources_cm = None
            self._resources = resources
        else:
            self._resources_cm = build_resources(
                check.opt_dict_param(resources, "resources", key_type=str)
            )
            self._resources = self._resources_cm.__enter__()  # pylint: disable=no-member
            self._resources_contain_cm = isinstance(self._resources, IContainsGenerator)
            self._cm_scope_entered = False

    def __enter__(self):
        if self._resources_cm:
            self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        if self._resources_cm:
            self._resources_cm.__exit__(*exc)  # pylint: disable=no-member

    def __del__(self):
        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            self._resources_cm.__exit__(None, None, None)  # pylint: disable=no-member

    @property
    def has_input_name(self) -> bool:
        """If we're the InputContext is being used to load the result of a run from outside the run,
        then it won't have an input name."""
        return self._name is not None

    @property
    def name(self) -> str:
        if self._name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access name, "
                "but it was not provided when constructing the InputContext"
            )

        return self._name

    @property
    def pipeline_name(self) -> str:
        if self._pipeline_name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access pipeline_name, "
                "but it was not provided when constructing the InputContext"
            )

        return self._pipeline_name

    @property
    def solid_def(self) -> "SolidDefinition":
        if self._solid_def is None:
            raise DagsterInvariantViolationError(
                "Attempting to access solid_def, "
                "but it was not provided when constructing the InputContext"
            )

        return self._solid_def

    @property
    def op_def(self) -> "OpDefinition":
        if self._solid_def is None:
            raise DagsterInvariantViolationError(
                "Attempting to access op_def, "
                "but it was not provided when constructing the InputContext"
            )

        return cast(OpDefinition, self._solid_def)

    @property
    def config(self) -> Any:
        return self._config

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        return self._metadata

    @property
    def upstream_output(self) -> Optional["OutputContext"]:
        return self._upstream_output

    @property
    def dagster_type(self) -> "DagsterType":
        if self._dagster_type is None:
            raise DagsterInvariantViolationError(
                "Attempting to access dagster_type, "
                "but it was not provided when constructing the InputContext"
            )

        return self._dagster_type

    @property
    def log(self) -> "DagsterLogManager":
        if self._log is None:
            raise DagsterInvariantViolationError(
                "Attempting to access log, "
                "but it was not provided when constructing the InputContext"
            )

        return self._log

    @property
    def resource_config(self) -> Optional[Dict[str, Any]]:
        return self._resource_config

    @property
    def resources(self) -> Any:
        if self._resources is None:
            raise DagsterInvariantViolationError(
                "Attempting to access resources, "
                "but it was not provided when constructing the InputContext"
            )

        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_input_context(...) as context:`"
            )
        return self._resources

    @property
    def asset_key(self) -> Optional[AssetKey]:
        matching_input_defs = [
            input_def
            for input_def in cast(SolidDefinition, self._solid_def).input_defs
            if input_def.name == self.name
        ]
        check.invariant(len(matching_input_defs) == 1)
        return matching_input_defs[0].get_asset_key(self)

    @property
    def step_context(self) -> "StepExecutionContext":
        if self._step_context is None:
            raise DagsterInvariantViolationError(
                "Attempting to access step_context, "
                "but it was not provided when constructing the InputContext"
            )

        return self._step_context

    @property
    def has_partition_key(self) -> bool:
        """Whether the current run is a partitioned run"""
        return self.step_context.has_partition_key

    @property
    def partition_key(self) -> str:
        """The partition key for the current run.

        Raises an error if the current run is not a partitioned run.
        """
        return self.step_context.partition_key


def build_input_context(
    name: Optional[str] = None,
    config: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
    upstream_output: Optional["OutputContext"] = None,
    dagster_type: Optional["DagsterType"] = None,
    resource_config: Optional[Dict[str, Any]] = None,
    resources: Optional[Dict[str, Any]] = None,
    op_def: Optional[OpDefinition] = None,
) -> "InputContext":
    """Builds input context from provided parameters.

    ``build_input_context`` can be used as either a function, or a context manager. If resources
    that are also context managers are provided, then ``build_input_context`` must be used as a
    context manager.

    Args:
        name (Optional[str]): The name of the input that we're loading.
        config (Optional[Any]): The config attached to the input that we're loading.
        metadata (Optional[Dict[str, Any]]): A dict of metadata that is assigned to the
            InputDefinition that we're loading for.
        upstream_output (Optional[OutputContext]): Info about the output that produced the object
            we're loading.
        dagster_type (Optional[DagsterType]): The type of this input.
        resource_config (Optional[Dict[str, Any]]): The resource config to make available from the
            input context. This usually corresponds to the config provided to the resource that
            loads the input manager.
        resources (Optional[Dict[str, Any]]): The resources to make available from the context.
            For a given key, you can provide either an actual instance of an object, or a resource
            definition.
        asset_key (Optional[AssetKey]): The asset key attached to the InputDefinition.
        op_def (Optional[OpDefinition]): The definition of the op that's loading the input.

    Examples:

        .. code-block:: python

            build_input_context()

            with build_input_context(resources={"foo": context_manager_resource}) as context:
                do_something
    """
    from dagster.core.execution.context.output import OutputContext
    from dagster.core.types.dagster_type import DagsterType
    from dagster.core.execution.context_creation_pipeline import initialize_console_manager

    name = check.opt_str_param(name, "name")
    metadata = check.opt_dict_param(metadata, "metadata", key_type=str)
    upstream_output = check.opt_inst_param(upstream_output, "upstream_output", OutputContext)
    dagster_type = check.opt_inst_param(dagster_type, "dagster_type", DagsterType)
    resource_config = check.opt_dict_param(resource_config, "resource_config", key_type=str)
    resources = check.opt_dict_param(resources, "resources", key_type=str)
    op_def = check.opt_inst_param(op_def, "op_def", OpDefinition)

    return InputContext(
        name=name,
        pipeline_name=None,
        config=config,
        metadata=metadata,
        upstream_output=upstream_output,
        dagster_type=dagster_type,
        log_manager=initialize_console_manager(None),
        resource_config=resource_config,
        resources=resources,
        step_context=None,
        op_def=op_def,
    )
