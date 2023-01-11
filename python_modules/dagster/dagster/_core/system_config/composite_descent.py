from typing import NamedTuple, Optional

import dagster._check as check
from dagster._config import EvaluateValueResult, process_config
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.run_config import define_solid_dictionary_cls
from dagster._core.errors import (
    DagsterConfigMappingFunctionError,
    DagsterInvalidConfigError,
    user_code_error_boundary,
)
from dagster._core.system_config.objects import OpConfig
from dagster._utils.merger import merge_dicts


class OpConfigEntry(
    NamedTuple("_SolidConfigEntry", [("handle", NodeHandle), ("solid_config", OpConfig)])
):
    def __new__(cls, handle: NodeHandle, solid_config: OpConfig):
        return super(OpConfigEntry, cls).__new__(
            cls,
            check.inst_param(handle, "handle", NodeHandle),
            check.inst_param(solid_config, "solid_config", OpConfig),
        )


class DescentStack(
    NamedTuple(
        "_DescentStack", [("pipeline_def", PipelineDefinition), ("handle", Optional[NodeHandle])]
    )
):
    def __new__(cls, pipeline_def: PipelineDefinition, handle: Optional[NodeHandle]):
        return super(DescentStack, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition),
            handle=check.opt_inst_param(handle, "handle", NodeHandle),
        )

    @property
    def current_container(self):
        return self.current_solid.definition if self.handle else self.pipeline_def.graph

    @property
    def current_solid(self):
        check.invariant(self.handle)
        return self.pipeline_def.get_solid(self.handle)

    @property
    def current_handle_str(self):
        return check.not_none(self.handle).to_string()

    def descend(self, solid):
        return self._replace(handle=NodeHandle(solid.name, parent=self.handle))


def composite_descent(pipeline_def, solids_config, resource_defs):
    """
    This function is responsible for constructing the dictionary
    of SolidConfig (indexed by handle) that will be passed into the
    ResolvedRunConfig. Critically this is the codepath that manages config mapping,
    where the runtime calls into user-defined config mapping functions to
    produce config for child solids of composites.

    Args:
        pipeline_def (PipelineDefinition): PipelineDefinition
        solids_config (dict): Configuration for the solids in the pipeline. The "solids" entry
            of the run_config. Assumed to have already been validated.

    Returns:
        Dict[str, SolidConfig]: A dictionary mapping string representations of NodeHandles to
            SolidConfig objects. It includes an entry for solids at every level of the
            composite tree - i.e. not just leaf solids, but composite solids as well
    """
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    check.dict_param(solids_config, "solids_config")
    check.dict_param(resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition)

    # If top-level graph has config mapping, apply that config mapping before descending.
    if pipeline_def.graph.has_config_mapping:
        solids_config = _apply_top_level_config_mapping(
            pipeline_def,
            solids_config,
            resource_defs,
            pipeline_def.is_job,  # pylint: disable=protected-access
        )

    return {
        handle.to_string(): solid_config
        for handle, solid_config in _composite_descent(
            parent_stack=DescentStack(pipeline_def, None),
            solids_config_dict=solids_config,
            resource_defs=resource_defs,
            is_using_graph_job_op_apis=pipeline_def.is_job,  # pylint: disable=protected-access
            asset_layer=pipeline_def.asset_layer,
        )
    }


def _composite_descent(
    parent_stack, solids_config_dict, resource_defs, is_using_graph_job_op_apis, asset_layer
):
    """
    The core implementation of composite_descent. This yields a stream of
    SolidConfigEntry. This is used by composite_descent to construct a
    dictionary.

    It descends over the entire solid hierarchy, constructing an entry
    for every handle. If it encounters a composite solid instance
    with a config mapping, it will invoke that config mapping fn,
    producing the config that is necessary to configure the child solids.

    This process unrolls recursively as you descend down the tree.
    """
    for solid in parent_stack.current_container.solids:
        current_stack = parent_stack.descend(solid)
        current_handle = current_stack.handle

        current_solid_config = solids_config_dict.get(solid.name, {})

        # the base case
        if isinstance(solid.definition, OpDefinition):
            config_mapped_solid_config = solid.definition.apply_config_mapping(
                {"config": current_solid_config.get("config")}
            )
            if not config_mapped_solid_config.success:
                raise DagsterInvalidConfigError(
                    f"Error in config for {solid.describe_node()}".format(solid.name),
                    config_mapped_solid_config.errors,
                    config_mapped_solid_config,
                )

            complete_config_object = merge_dicts(
                current_solid_config, config_mapped_solid_config.value
            )
            yield OpConfigEntry(current_handle, OpConfig.from_dict(complete_config_object))
            continue

        graph_def = check.inst(solid.definition, GraphDefinition)

        yield OpConfigEntry(
            current_handle,
            OpConfig.from_dict(
                {
                    "inputs": current_solid_config.get("inputs"),
                    "outputs": current_solid_config.get("outputs"),
                }
            ),
        )
        node_key = "ops" if is_using_graph_job_op_apis else "solids"

        # If there is a config mapping, invoke it and get the descendent solids
        # config that way. Else just grabs the solids entry of the current config
        solids_dict = (
            _get_mapped_solids_dict(
                solid,
                graph_def,
                current_stack,
                current_solid_config,
                resource_defs,
                is_using_graph_job_op_apis,
                asset_layer,
            )
            if graph_def.has_config_mapping
            else current_solid_config.get(node_key, {})
        )

        yield from _composite_descent(
            current_stack, solids_dict, resource_defs, is_using_graph_job_op_apis, asset_layer
        )


def _apply_top_level_config_mapping(
    pipeline_def,
    outer_config,
    resource_defs,
    is_using_graph_job_op_apis,
):
    graph_def = pipeline_def.graph

    if not graph_def.has_config_mapping:
        return outer_config

    else:
        mapped_config_evr = graph_def.apply_config_mapping(outer_config)
        if not mapped_config_evr.success:
            raise DagsterInvalidConfigError(
                "Error in config for graph {}".format(graph_def.name),
                mapped_config_evr.errors,
                outer_config,
            )

        with user_code_error_boundary(
            DagsterConfigMappingFunctionError, _get_top_level_error_lambda(pipeline_def)
        ):
            mapped_graph_config = graph_def.config_mapping.resolve_from_validated_config(
                mapped_config_evr.value.get("config", {})
            )

        # Dynamically construct the type that the output of the config mapping function will
        # be evaluated against

        type_to_evaluate_against = define_solid_dictionary_cls(
            solids=graph_def.solids,
            ignored_solids=None,
            dependency_structure=graph_def.dependency_structure,
            resource_defs=resource_defs,
            is_using_graph_job_op_apis=is_using_graph_job_op_apis,
            asset_layer=pipeline_def.asset_layer,
        )

        # process against that new type

        evr = process_config(type_to_evaluate_against, mapped_graph_config)

        if not evr.success:
            raise_top_level_config_error(pipeline_def, mapped_graph_config, evr)

        return evr.value


def _get_mapped_solids_dict(
    composite,
    graph_def,
    current_stack,
    current_solid_config,
    resource_defs,
    is_using_graph_job_op_apis,
    asset_layer,
):
    # the spec of the config mapping function is that it takes the dictionary at:
    # solid_name:
    #    config: {dict_passed_to_user}

    # and it returns the dictionary rooted at solids
    # solid_name:
    #    solids: {return_value_of_config_fn}

    # We must call the config mapping function and then validate it against
    # the child schema.

    # apply @configured config mapping to the composite's incoming config before we get to the
    # composite's own config mapping process
    config_mapped_solid_config = graph_def.apply_config_mapping(current_solid_config)
    if not config_mapped_solid_config.success:
        raise DagsterInvalidConfigError(
            "Error in config for composite solid {}".format(composite.name),
            config_mapped_solid_config.errors,
            config_mapped_solid_config,
        )

    with user_code_error_boundary(
        DagsterConfigMappingFunctionError, _get_error_lambda(current_stack)
    ):
        mapped_solids_config = graph_def.config_mapping.resolve_from_validated_config(
            config_mapped_solid_config.value.get("config", {})
        )

    # Dynamically construct the type that the output of the config mapping function will
    # be evaluated against

    # diff original graph and the subselected graph to find nodes to ignore so the system knows to
    # skip the validation then when config mapping generates values where the nodes are not selected
    ignored_solids = graph_def.get_top_level_omitted_nodes() if graph_def.is_subselected else None

    type_to_evaluate_against = define_solid_dictionary_cls(
        solids=graph_def.solids,
        ignored_solids=ignored_solids,
        dependency_structure=graph_def.dependency_structure,
        parent_handle=current_stack.handle,
        resource_defs=resource_defs,
        is_using_graph_job_op_apis=is_using_graph_job_op_apis,
        asset_layer=asset_layer,
    )

    # process against that new type

    evr = process_config(type_to_evaluate_against, mapped_solids_config)

    if not evr.success:
        raise_composite_descent_config_error(current_stack, mapped_solids_config, evr)

    return evr.value


def _get_error_lambda(current_stack):
    return lambda: (
        "The config mapping function on {described_node} in {described_target} "
        "has thrown an unexpected error during its execution. The definition is "
        'instantiated at stack "{stack_str}".'
    ).format(
        described_node=current_stack.current_solid.describe_node(),
        described_target=current_stack.pipeline_def.describe_target(),
        stack_str=":".join(current_stack.handle.path),
    )


def _get_top_level_error_lambda(pipeline_def):
    return (
        lambda: f"The config mapping function on top-level graph {pipeline_def.graph.name} in job {pipeline_def.name} has thrown an unexpected error during its execution."
    )


def raise_top_level_config_error(pipeline_def, failed_config_value, evr):
    message = (
        f"In pipeline '{pipeline_def.name}', top level graph '{pipeline_def.graph.name}' has a "
        "configuration error."
    )

    raise DagsterInvalidConfigError(message, evr.errors, failed_config_value)


def raise_composite_descent_config_error(descent_stack, failed_config_value, evr):
    check.inst_param(descent_stack, "descent_stack", DescentStack)
    check.inst_param(evr, "evr", EvaluateValueResult)

    solid = descent_stack.current_solid
    message = "In pipeline {pipeline_name} at stack {stack}: \n".format(
        pipeline_name=descent_stack.pipeline_def.name,
        stack=":".join(descent_stack.handle.path),
    )
    message += (
        'Solid "{solid_name}" with definition "{solid_def_name}" has a '
        "configuration error. "
        "It has produced config a via its config_fn that fails to "
        "pass validation in the solids that it contains. "
        "This indicates an error in the config mapping function itself. It must "
        "produce correct config for its constiuent solids in all cases. The correct "
        "resolution is to fix the mapping function. Details on the error (and the paths "
        'on this error are relative to config mapping function "root", not the entire document): '
    ).format(
        solid_name=solid.name,
        solid_def_name=solid.definition.name,
    )

    raise DagsterInvalidConfigError(message, evr.errors, failed_config_value)
