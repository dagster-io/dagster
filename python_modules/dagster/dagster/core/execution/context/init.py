from collections import namedtuple
from typing import Any, Dict, Optional, Set

from dagster import check
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.resource import ResourceDefinition, ScopedResourcesBuilder
from dagster.core.instance import DagsterInstance
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.pipeline_run import PipelineRun


class InitResourceContext(
    namedtuple(
        "InitResourceContext",
        (
            "resource_config resource_def pipeline_run log_manager resources "
            "instance_for_backwards_compat pipeline_def_for_backwards_compat"
        ),
    )
):
    """Resource-specific initialization context.

    Attributes:
        resource_config (Any): The configuration data provided by the environment config. The schema
            for this data is defined by the ``config_field`` argument to
            :py:class:`ResourceDefinition`.
        resource_def (ResourceDefinition): The definition of the resource currently being
            constructed.
        pipeline_run (PipelineRun): The pipeline run in context.
        run_id (str): The id for this run of the pipeline.
        log_manager (DagsterLogManager): The log manager for this run of the pipeline
        resources (ScopedResources): The resources that are available to the resource that we are
            initalizing.
    """

    def __new__(
        cls,
        resource_config: Any,
        resource_def: ResourceDefinition,
        pipeline_run: PipelineRun,
        log_manager: Optional[DagsterLogManager] = None,
        resource_instance_dict: Optional[Dict[str, Any]] = None,
        required_resource_keys: Optional[Set[str]] = None,
        instance_for_backwards_compat: Optional[DagsterInstance] = None,
        pipeline_def_for_backwards_compat: Optional[PipelineDefinition] = None,
    ):
        check.opt_dict_param(resource_instance_dict, "resource_instance_dict")
        required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys"
        )

        scoped_resources_builder = ScopedResourcesBuilder(resource_instance_dict)

        return super(InitResourceContext, cls).__new__(
            cls,
            resource_config,
            check.inst_param(resource_def, "resource_def", ResourceDefinition),
            check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
            check.opt_inst_param(log_manager, "log_manager", DagsterLogManager),
            resources=scoped_resources_builder.build(required_resource_keys),
            # The following are used internally for adapting intermediate storage defs to resources
            instance_for_backwards_compat=check.opt_inst_param(
                instance_for_backwards_compat, "instance_for_backwards_compat", DagsterInstance
            ),
            pipeline_def_for_backwards_compat=check.opt_inst_param(
                pipeline_def_for_backwards_compat,
                "pipeline_def_for_backwards_compat",
                PipelineDefinition,
            ),
        )

    @property
    def log(self) -> DagsterLogManager:
        return self.log_manager

    @property
    def run_id(self) -> str:
        return self.pipeline_run.run_id

    def replace_config(self, config: Any) -> "InitResourceContext":
        return InitResourceContext(
            resource_config=config,
            resource_def=self.resource_def,
            pipeline_run=self.pipeline_run,
            log_manager=self.log_manager,
            instance_for_backwards_compat=self.instance_for_backwards_compat,
        )
