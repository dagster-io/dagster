from typing import Any, Mapping, Optional, Union

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.resource_definition import (
    IContainsGenerator,
    ResourceDefinition,
    Resources,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun


class InitResourceContext:
    """The context object available as the argument to the initialization function of a :py:class:`dagster.ResourceDefinition`.

    Users should not instantiate this object directly. To construct an `InitResourceContext` for testing purposes, use :py:func:`dagster.build_init_resource_context`.

    Example:
        .. code-block:: python

            from dagster import resource, InitResourceContext

            @resource
            def the_resource(init_context: InitResourceContext):
                init_context.log.info("Hello, world!")
    """

    def __init__(
        self,
        resource_config: Any,
        resources: Resources,
        resource_def: Optional[ResourceDefinition] = None,
        instance: Optional[DagsterInstance] = None,
        dagster_run: Optional[DagsterRun] = None,
        log_manager: Optional[DagsterLogManager] = None,
    ):
        self._resource_config = resource_config
        self._resource_def = resource_def
        self._log_manager = log_manager
        self._instance = instance
        self._resources = resources
        self._dagster_run = dagster_run

    @public
    @property
    def resource_config(self) -> Any:
        """The configuration data provided by the run config. The schema
        for this data is defined by the ``config_field`` argument to
        :py:class:`ResourceDefinition`.
        """
        return self._resource_config

    @public
    @property
    def resource_def(self) -> Optional[ResourceDefinition]:
        """The definition of the resource currently being constructed."""
        return self._resource_def

    @public
    @property
    def resources(self) -> Resources:
        """The resources that are available to the resource that we are initalizing."""
        return self._resources

    @public
    @property
    def instance(self) -> Optional[DagsterInstance]:
        """The Dagster instance configured for the current execution context."""
        return self._instance

    @property
    def dagster_run(self) -> Optional[DagsterRun]:
        """The dagster run to use. When initializing resources outside of execution context, this will be None.
        """
        return self._dagster_run

    @public
    @property
    def log(self) -> Optional[DagsterLogManager]:
        """The Dagster log manager configured for the current execution context."""
        return self._log_manager

    # backcompat: keep around this property from when InitResourceContext used to be a NamedTuple
    @public
    @property
    def log_manager(self) -> Optional[DagsterLogManager]:
        """The log manager for this run of the job."""
        return self._log_manager

    @public
    @property
    def run_id(self) -> Optional[str]:
        """The id for this run of the job or pipeline. When initializing resources outside of
        execution context, this will be None.
        """
        return self.dagster_run.run_id if self.dagster_run else None

    def replace_config(self, config: Any) -> "InitResourceContext":
        return InitResourceContext(
            resource_config=config,
            resources=self.resources,
            instance=self.instance,
            resource_def=self.resource_def,
            dagster_run=self.dagster_run,
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
        resources: Optional[Union[Resources, Mapping[str, Any]]],
        instance: Optional[DagsterInstance],
    ):
        from dagster._core.execution.api import ephemeral_instance_if_missing
        from dagster._core.execution.build_resources import (
            build_resources,
            wrap_resources_for_execution,
        )
        from dagster._core.execution.context_creation_job import initialize_console_manager

        self._instance_provided = (
            check.opt_inst_param(instance, "instance", DagsterInstance) is not None
        )
        # Construct ephemeral instance if missing
        self._instance_cm = ephemeral_instance_if_missing(instance)
        # Pylint can't infer that the ephemeral_instance context manager has an __enter__ method,
        # so ignore lint error
        instance = self._instance_cm.__enter__()

        if isinstance(resources, Resources):
            check.failed("Should not have a Resources object directly from this initialization")

        self._resource_defs = wrap_resources_for_execution(
            check.opt_mapping_param(resources, "resources")
        )

        self._resources_cm = build_resources(self._resource_defs, instance=instance)
        resources = self._resources_cm.__enter__()
        self._resources_contain_cm = isinstance(resources, IContainsGenerator)

        self._cm_scope_entered = False
        super(UnboundInitResourceContext, self).__init__(
            resource_config=resource_config,
            resources=resources,
            resource_def=None,
            instance=instance,
            dagster_run=None,
            log_manager=initialize_console_manager(None),
        )

    def __enter__(self):
        self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        self._resources_cm.__exit__(*exc)
        if self._instance_provided:
            self._instance_cm.__exit__(*exc)

    def __del__(self):
        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            self._resources_cm.__exit__(None, None, None)
        if self._instance_provided and not self._cm_scope_entered:
            self._instance_cm.__exit__(None, None, None)

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
        """The resources that are available to the resource that we are initalizing."""
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
    config: Optional[Mapping[str, Any]] = None,
    resources: Optional[Mapping[str, Any]] = None,
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
        resource_config=check.opt_mapping_param(config, "config", key_type=str),
        instance=check.opt_inst_param(instance, "instance", DagsterInstance),
        resources=check.opt_mapping_param(resources, "resources", key_type=str),
    )
