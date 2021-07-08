from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError

if TYPE_CHECKING:
    from .output import OutputContext
    from dagster.core.definitions import SolidDefinition
    from dagster.core.log_manager import DagsterLogManager
    from dagster.core.types.dagster_type import DagsterType
    from dagster.core.execution.context.system import StepExecutionContext
    from dagster.core.definitions.resource import Resources


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
    ):
        from dagster.core.definitions.resource import Resources, IContainsGenerator
        from dagster.core.execution.build_resources import build_resources

        self._name = name
        self._pipeline_name = pipeline_name
        self._solid_def = solid_def
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
    def name(self) -> Optional[str]:
        return self._name

    @property
    def pipeline_name(self) -> Optional[str]:
        return self._pipeline_name

    @property
    def solid_def(self) -> Optional["SolidDefinition"]:
        return self._solid_def

    @property
    def config(self) -> Optional[Any]:
        return self._config

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        return self._metadata

    @property
    def upstream_output(self) -> Optional["OutputContext"]:
        return self._upstream_output

    @property
    def dagster_type(self) -> Optional["DagsterType"]:
        return self._dagster_type

    @property
    def log(self) -> Optional["DagsterLogManager"]:
        return self._log

    @property
    def resource_config(self) -> Optional[Dict[str, Any]]:
        return self._resource_config

    @property
    def resources(self) -> Optional["Resources"]:
        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_input_context(...) as context:`"
            )
        return self._resources

    @property
    def step_context(self) -> Optional["StepExecutionContext"]:
        return self._step_context


def build_input_context(
    name: Optional[str] = None,
    config: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
    upstream_output: Optional["OutputContext"] = None,
    dagster_type: Optional["DagsterType"] = None,
    resource_config: Optional[Dict[str, Any]] = None,
    resources: Optional[Dict[str, Any]] = None,
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

    return InputContext(
        name=name,
        pipeline_name=None,
        solid_def=None,
        config=config,
        metadata=metadata,
        upstream_output=upstream_output,
        dagster_type=dagster_type,
        log_manager=initialize_console_manager(None),
        resource_config=resource_config,
        resources=resources,
        step_context=None,
    )
