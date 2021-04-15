from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional, cast

from dagster.core.execution.plan.utils import build_resources_for_manager
from dagster.core.storage.tags import MEMOIZED_RUN_TAG

if TYPE_CHECKING:
    from dagster.core.execution.context.system import StepExecutionContext
    from dagster.core.definitions.resource import Resources
    from dagster.core.types.dagster_type import DagsterType
    from dagster.core.definitions import SolidDefinition, PipelineDefinition
    from dagster.core.log_manager import DagsterLogManager
    from dagster.core.system_config.objects import EnvironmentConfig
    from dagster.core.execution.plan.plan import ExecutionPlan
    from dagster.core.execution.plan.outputs import StepOutputHandle
    from dagster.core.log_manager import DagsterLogManager


class OutputContext(
    NamedTuple(
        "_OutputContext",
        [
            ("step_key", str),
            ("name", str),
            ("pipeline_name", str),
            ("run_id", Optional[str]),
            ("metadata", Optional[Dict[str, Any]]),
            ("mapping_key", Optional[str]),
            ("config", Optional[Any]),
            ("solid_def", Optional["SolidDefinition"]),
            ("dagster_type", Optional["DagsterType"]),
            ("log", Optional["DagsterLogManager"]),
            ("version", Optional[str]),
            ("resource_config", Optional[Dict[str, Any]]),
            ("resources", Optional["Resources"]),
            ("step_context", Optional["StepExecutionContext"]),
        ],
    )
):
    """
    The context object that is available to the `handle_output` method of an :py:class:`IOManager`.

    Attributes:
        step_key (str): The step_key for the compute step that produced the output.
        name (str): The name of the output that produced the output.
        pipeline_name (str): The name of the pipeline definition.
        run_id (Optional[str]): The id of the run that produced the output.
        metadata (Optional[Dict[str, Any]]): A dict of the metadata that is assigned to the
            OutputDefinition that produced the output.
        mapping_key (Optional[str]): The key that identifies a unique mapped output. None for regular outputs.
        config (Optional[Any]): The configuration for the output.
        solid_def (Optional[SolidDefinition]): The definition of the solid that produced the output.
        dagster_type (Optional[DagsterType]): The type of this output.
        log (Optional[DagsterLogManager]): The log manager to use for this output.
        version (Optional[str]): (Experimental) The version of the output.
        resource_config (Optional[Dict[str, Any]]): The config associated with the resource that
            initializes the RootInputManager.
        resources (Optional[Resources]): The resources required by the output manager, specified by the
            `required_resource_keys` parameter.
    """

    def __new__(
        cls,
        step_key: str,
        name: str,
        pipeline_name: str,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mapping_key: Optional[str] = None,
        config: Optional[Any] = None,
        solid_def: Optional["SolidDefinition"] = None,
        dagster_type: Optional["DagsterType"] = None,
        log_manager: Optional["DagsterLogManager"] = None,
        version: Optional[str] = None,
        resource_config: Optional[Dict[str, Any]] = None,
        resources: Optional["Resources"] = None,
        step_context: Optional["StepExecutionContext"] = None,
    ):
        return super(OutputContext, cls).__new__(
            cls,
            step_key=step_key,
            name=name,
            pipeline_name=pipeline_name,
            run_id=run_id,
            metadata=metadata,
            mapping_key=mapping_key,
            config=config,
            solid_def=solid_def,
            dagster_type=dagster_type,
            log=log_manager,
            version=version,
            resource_config=resource_config,
            resources=resources,
            step_context=step_context,
        )

    def get_run_scoped_output_identifier(self) -> List[str]:
        """Utility method to get a collection of identifiers that as a whole represent a unique
        step output.

        The unique identifier collection consists of

        - ``run_id``: the id of the run which generates the output.
            Note: This method also handles the re-execution memoization logic. If the step that
            generates the output is skipped in the re-execution, the ``run_id`` will be the id
            of its parent run.
        - ``step_key``: the key for a compute step.
        - ``name``: the name of the output. (default: 'result').

        Returns:
            List[str, ...]: A list of identifiers, i.e. run id, step key, and output name
        """
        run_id = cast(str, self.run_id)
        if self.mapping_key:
            return [run_id, self.step_key, self.name, self.mapping_key]

        return [run_id, self.step_key, self.name]


def get_output_context(
    execution_plan: "ExecutionPlan",
    pipeline_def: "PipelineDefinition",
    environment_config: "EnvironmentConfig",
    step_output_handle: "StepOutputHandle",
    run_id: Optional[str] = None,
    log_manager: Optional["DagsterLogManager"] = None,
    step_context: Optional["StepExecutionContext"] = None,
) -> "OutputContext":
    """
    Args:
        run_id (str): The run ID of the run that produced the output, not necessarily the run that
            the context will be used in.
    """

    step = execution_plan.get_step_by_key(step_output_handle.step_key)
    # get config
    solid_config = environment_config.solids.get(step.solid_handle.to_string())
    outputs_config = solid_config.outputs

    if outputs_config:
        output_config = outputs_config.get_output_manager_config(step_output_handle.output_name)
    else:
        output_config = None

    step_output = execution_plan.get_step_output(step_output_handle)
    output_def = pipeline_def.get_solid(step_output.solid_handle).output_def_named(step_output.name)

    io_manager_key = output_def.io_manager_key
    resource_config = environment_config.resources[io_manager_key].config

    resources = build_resources_for_manager(io_manager_key, step_context) if step_context else None

    return OutputContext(
        step_key=step_output_handle.step_key,
        name=step_output_handle.output_name,
        pipeline_name=pipeline_def.name,
        run_id=run_id,
        metadata=output_def.metadata,
        mapping_key=step_output_handle.mapping_key,
        config=output_config,
        solid_def=pipeline_def.get_solid(step.solid_handle).definition,
        dagster_type=output_def.dagster_type,
        log_manager=log_manager,
        version=(
            _step_output_version(
                pipeline_def, execution_plan, environment_config, step_output_handle
            )
            if MEMOIZED_RUN_TAG in pipeline_def.tags
            else None
        ),
        step_context=step_context,
        resource_config=resource_config,
        resources=resources,
    )


def _step_output_version(
    pipeline_def: "PipelineDefinition",
    execution_plan: "ExecutionPlan",
    environment_config: "EnvironmentConfig",
    step_output_handle: "StepOutputHandle",
) -> Optional[str]:
    from dagster.core.execution.resolve_versions import resolve_step_output_versions

    step_output_versions = resolve_step_output_versions(
        pipeline_def, execution_plan, environment_config
    )
    return (
        step_output_versions[step_output_handle]
        if step_output_handle in step_output_versions
        else None
    )
