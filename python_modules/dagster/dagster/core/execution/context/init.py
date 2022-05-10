from typing import Any, Dict, Optional, Union

import dagster._check as check
from dagster.core.definitions.pipeline_definition import PipelineDefinition
from dagster.core.definitions.resource_definition import (
    IContainsGenerator,
    ResourceDefinition,
    Resources,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.instance import DagsterInstance
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.pipeline_run import PipelineRun


class InitResourceContext:
    """Resource-specific initialization context.

    Attributes:
        resource_config (Any): The configuration data provided by the run config. The schema
            for this data is defined by the ``config_field`` argument to
            :py:class:`ResourceDefinition`.
        resource_def (ResourceDefinition): The definition of the resource currently being
            constructed.
        log_manager (DagsterLogManager): The log manager for this run of the job or pipeline
        resources (ScopedResources): The resources that are available to the resource that we are
            initalizing.
        dagster_run (Optional[PipelineRun]): The dagster run to use. When initializing resources
            outside of execution context, this will be None.
        run_id (Optional[str]): The id for this run of the job or pipeline. When initializing resources
            outside of execution context, this will be None.
        pipeline_run (Optional[PipelineRun]): (legacy) The dagster run to use. When initializing resources
            outside of execution context, this will be None.

    """

    def __init__(
        self,
        resource_config: Any,
        resources: Resources,
        resource_def: Optional[ResourceDefinition] = None,
        instance: Optional[DagsterInstance] = None,
        dagster_run: Optional[PipelineRun] = None,
        pipeline_run: Optional[PipelineRun] = None,
        log_manager: Optional[DagsterLogManager] = None,
        pipeline_def_for_backwards_compat: Optional[PipelineDefinition] = None,
    ):

        if dagster_run and pipeline_run:
            raise DagsterInvariantViolationError(
                "Provided both ``dagster_run`` and ``pipeline_run`` to InitResourceContext "
                "initialization. Please provide one or the other."
            )
        self._resource_config = resource_config
        self._resource_def = resource_def
        self._log_manager = log_manager
        self._instance = instance
        self._resources = resources

        self._pipeline_def_for_backwards_compat = pipeline_def_for_backwards_compat
        self._dagster_run = dagster_run or pipeline_run

    @property
    def resource_config(self) -> Any:
        return self._resource_config

    @property
    def resource_def(self) -> Optional[ResourceDefinition]:
        return self._resource_def

    @property
    def resources(self) -> Resources:
        return self._resources

    @property
    def instance(self) -> Optional[DagsterInstance]:
        return self._instance

    @property
    def pipeline_def_for_backwards_compat(self) -> Optional[PipelineDefinition]:
        return self._pipeline_def_for_backwards_compat

    @property
    def dagster_run(self) -> Optional[PipelineRun]:
        return self._dagster_run

    @property
    def pipeline_run(self) -> Optional[PipelineRun]:
        return self.dagster_run

    @property
    def log(self) -> Optional[DagsterLogManager]:
        return self._log_manager

    # backcompat: keep around this property from when InitResourceContext used to be a NamedTuple
    @property
    def log_manager(self) -> Optional[DagsterLogManager]:
        return self._log_manager

    @property
    def run_id(self) -> Optional[str]:
        return self.pipeline_run.run_id if self.pipeline_run else None

    def replace_config(self, config: Any) -> "InitResourceContext":
        return InitResourceContext(
            resource_config=config,
            resources=self.resources,
            instance=self.instance,
            resource_def=self.resource_def,
            pipeline_run=self.pipeline_run,
            log_manager=self.log,
        )


class UnboundInitResourceContext(InitResourceContext):
    """Resource initialization context outputted by ``build_init_resource_context``.

    Represents a context whose config has not yet been validated against a resource definition,
    hence the inability to access the `resource_def` attribute. When an instance of
    ``UnboundInitResourceContext`` is passed to a resource invocation, config is validated,
    and it is subsumed into an `InitResourceContext`, which contains the resource_def validated
    against.
    """

    def __init__(
        self,
        resource_config: Any,
        resources: Optional[Union[Resources, Dict[str, Any]]],
        instance: Optional[DagsterInstance],
    ):
        from dagster.core.execution.api import ephemeral_instance_if_missing
        from dagster.core.execution.build_resources import build_resources
        from dagster.core.execution.context_creation_pipeline import initialize_console_manager

        self._instance_provided = (
            check.opt_inst_param(instance, "instance", DagsterInstance) is not None
        )
        # Construct ephemeral instance if missing
        self._instance_cm = ephemeral_instance_if_missing(instance)
        # Pylint can't infer that the ephemeral_instance context manager has an __enter__ method,
        # so ignore lint error
        instance = self._instance_cm.__enter__()  # pylint: disable=no-member

        # If we are provided with a Resources instance, then we do not need to initialize
        if isinstance(resources, Resources):
            self._resources_cm = None
        else:
            self._resources_cm = build_resources(
                check.opt_dict_param(resources, "resources", key_type=str), instance=instance
            )
            resources = self._resources_cm.__enter__()  # pylint: disable=no-member
            self._resources_contain_cm = isinstance(resources, IContainsGenerator)

        self._cm_scope_entered = False
        super(UnboundInitResourceContext, self).__init__(
            resource_config=resource_config,
            resources=resources,
            resource_def=None,
            instance=instance,
            pipeline_run=None,
            log_manager=initialize_console_manager(None),
            pipeline_def_for_backwards_compat=None,
        )

    def __enter__(self):
        self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        if self._resources_cm:
            self._resources_cm.__exit__(*exc)  # pylint: disable=no-member
        if self._instance_provided:
            self._instance_cm.__exit__(*exc)  # pylint: disable=no-member

    def __del__(self):
        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            self._resources_cm.__exit__(None, None, None)  # pylint: disable=no-member
        if self._instance_provided and not self._cm_scope_entered:
            self._instance_cm.__exit__(None, None, None)  # pylint: disable=no-member

    @property
    def resource_config(self) -> Any:
        return self._resource_config

    @property
    def resource_def(self) -> Optional[ResourceDefinition]:
        raise DagsterInvariantViolationError(
            "UnboundInitLoggerContext has not been validated against a logger definition."
        )

    @property
    def resources(self) -> Resources:
        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_init_resource_context(...) as context:`"
            )
        return self._resources

    @property
    def instance(self) -> Optional[DagsterInstance]:
        return self._instance

    @property
    def pipeline_def_for_backwards_compat(self) -> Optional[PipelineDefinition]:
        return None

    @property
    def pipeline_run(self) -> Optional[PipelineRun]:
        return None

    @property
    def log(self) -> Optional[DagsterLogManager]:
        return self._log_manager

    # backcompat: keep around this property from when InitResourceContext used to be a NamedTuple
    @property
    def log_manager(self) -> Optional[DagsterLogManager]:
        return self._log_manager

    @property
    def run_id(self) -> Optional[str]:
        return None


def build_init_resource_context(
    config: Optional[Dict[str, Any]] = None,
    resources: Optional[Dict[str, Any]] = None,
    instance: Optional[DagsterInstance] = None,
) -> InitResourceContext:
    """Builds resource initialization context from provided parameters.

    ``build_init_resource_context`` can be used as either a function or context manager. If there is a
    provided resource to ``build_init_resource_context`` that is a context manager, then it must be
    used as a context manager. This function can be used to provide the context argument to the
    invocation of a resource.

    Args:
        resources (Optional[Dict[str, Any]]): The resources to provide to the context. These can be
            either values or resource definitions.
        config (Optional[Any]): The resource config to provide to the context.
        instance (Optional[DagsterInstance]): The dagster instance configured for the context.
            Defaults to DagsterInstance.ephemeral().

    Examples:
        .. code-block:: python

            context = build_init_resource_context()
            resource_to_init(context)

            with build_init_resource_context(
                resources={"foo": context_manager_resource}
            ) as context:
                resource_to_init(context)

    """
    return UnboundInitResourceContext(
        resource_config=check.opt_dict_param(config, "config", key_type=str),
        instance=check.opt_inst_param(instance, "instance", DagsterInstance),
        resources=check.opt_dict_param(resources, "resources", key_type=str),
    )
