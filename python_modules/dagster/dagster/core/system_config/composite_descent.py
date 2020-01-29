from collections import namedtuple

from dagster import check
from dagster.config.evaluate_value_result import EvaluateValueResult
from dagster.config.validate import process_config
from dagster.core.definitions.dependency import SolidHandle
from dagster.core.definitions.environment_configs import define_solid_dictionary_cls
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.solid import CompositeSolidDefinition
from dagster.core.errors import (
    DagsterConfigMappingFunctionError,
    DagsterInvalidConfigError,
    user_code_error_boundary,
)
from dagster.core.execution.config import IRunConfig, RunConfig
from dagster.core.system_config.objects import SolidConfig


class SolidConfigEntry(namedtuple('_SolidConfigEntry', 'handle solid_config')):
    def __new__(cls, handle, solid_config):
        return super(SolidConfigEntry, cls).__new__(
            cls,
            check.inst_param(handle, 'handle', SolidHandle),
            check.inst_param(solid_config, 'solid_config', SolidConfig),
        )


class DescentStack(namedtuple('_DescentStack', 'pipeline_def handle')):
    def __new__(cls, pipeline_def, handle):
        return super(DescentStack, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            handle=check.opt_inst_param(handle, 'handle', SolidHandle),
        )

    @property
    def current_container(self):
        return self.current_solid.definition if self.handle else self.pipeline_def

    @property
    def current_solid(self):
        check.invariant(self.handle)
        return self.pipeline_def.get_solid(self.handle)

    @property
    def current_handle_str(self):
        check.invariant(self.handle)
        return self.handle.to_string()

    def descend(self, solid):
        return self._replace(
            handle=SolidHandle(solid.name, solid.definition.name, parent=self.handle)
        )


def composite_descent(pipeline_def, solids_config, run_config=None):
    '''
    This function is responsible for constructing the dictionary
    of SolidConfig (indexed by handle) that will be passed into the
    EnvironmentConfig. Critically this is the codepath that manages config mapping,
    where the runtime calls into user-defined config mapping functions to
    produce config for child solids of composites.

    pipeline_def (PipelineDefintiion): PipelineDefinition
    solids_config (dict): Configuration for the solids in the pipeline. The "solids" entry
    of the environment_dict. Assumed to have already been validated.
    '''
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(solids_config, 'solids_config')

    run_config = (
        RunConfig()
        if run_config is None
        else check.inst_param(run_config, 'run_config', IRunConfig)
    )

    return {
        handle.to_string(): solid_config
        for handle, solid_config in _composite_descent(
            parent_stack=DescentStack(pipeline_def, None), solids_config_dict=solids_config,
        )
    }


def _composite_descent(parent_stack, solids_config_dict):
    '''
    The core implementation of composite_descent. This yields a stream of
    SolidConfigEntry. This is used by composite_descent to construct a
    dictionary.

    It descends over the entire solid hierarchy, constructing an entry
    for every handle. If it encounters a composite solid instance
    with a config mapping, it will invoke that config mapping fn,
    producing the config that is necessary to configure the child solids.

    This process unrolls recursively as you descend down the tree.
    '''

    for solid in parent_stack.current_container.solids:

        current_stack = parent_stack.descend(solid)
        current_handle = current_stack.handle

        current_solid_config = solids_config_dict.get(solid.name, {})

        # the base case
        if not isinstance(solid.definition, CompositeSolidDefinition):
            yield SolidConfigEntry(current_handle, SolidConfig.from_dict(current_solid_config))
            continue

        composite_def = check.inst(solid.definition, CompositeSolidDefinition)

        yield SolidConfigEntry(
            current_handle,
            SolidConfig.from_dict(
                {
                    'inputs': current_solid_config.get('inputs'),
                    'outputs': current_solid_config.get('outputs'),
                }
            ),
        )

        # If there is a config mapping, invoke it and get the descendent solids
        # config that way. Else just grabs the solids entry of the current config
        solids_dict = (
            _get_mapped_solids_dict(composite_def, current_stack, current_solid_config)
            if composite_def.config_mapping
            else current_solid_config.get('solids', {})
        )

        for sce in _composite_descent(current_stack, solids_dict):
            yield sce


def _get_mapped_solids_dict(composite_def, current_stack, current_solid_config):
    # the spec of the config mapping function is that it takes the dictionary at:
    # solid_name:
    #    config: {dict_passed_to_user}

    # and it returns the dictionary rooted at solids
    # solid_name:
    #    solids: {return_value_of_config_fn}

    # We must call the config mapping function and then validate it against
    # the child schema.

    with user_code_error_boundary(
        DagsterConfigMappingFunctionError, _get_error_lambda(current_stack)
    ):
        mapped_solids_config = composite_def.config_mapping.config_fn(
            current_solid_config.get('config', {})
        )

    # Dynamically construct the type that the output of the config mapping function will
    # be evaluated against

    type_to_evaluate_against = define_solid_dictionary_cls(
        composite_def.solids, composite_def.dependency_structure, current_stack.handle
    )

    # process against that new type

    evr = process_config(type_to_evaluate_against, mapped_solids_config)

    if not evr.success:
        raise_composite_descent_config_error(current_stack, mapped_solids_config, evr)

    return evr.value


def _get_error_lambda(current_stack):
    return lambda: (
        'The config mapping function on the composite solid definition '
        '"{definition_name}" at solid "{solid_name}" in pipeline "{pipeline_name}" '
        'has thrown an unexpected error during its execution. The definition is '
        'instantiated at stack "{stack_str}".'
    ).format(
        definition_name=current_stack.current_solid.definition.name,
        solid_name=current_stack.current_solid.name,
        pipeline_name=current_stack.pipeline_def.name,
        stack_str=':'.join(current_stack.handle.path),
    )


def raise_composite_descent_config_error(descent_stack, failed_config_value, evr):
    check.inst_param(descent_stack, 'descent_stack', DescentStack)
    check.inst_param(evr, 'evr', EvaluateValueResult)

    solid = descent_stack.current_solid
    message = 'In pipeline {pipeline_name} at stack {stack}: \n'.format(
        pipeline_name=descent_stack.pipeline_def.name, stack=':'.join(descent_stack.handle.path),
    )
    message += (
        'Solid "{solid_name}" with definition "{solid_def_name}" has a '
        'configuration error. '
        'It has produced config a via its config_fn that fails to '
        'pass validation in the solids that it contains. '
        'This indicates an error in the config mapping function itself. It must '
        'produce correct config for its constiuent solids in all cases. The correct '
        'resolution is to fix the mapping function. Details on the error (and the paths '
        'on this error are relative to config mapping function "root", not the entire document): '
    ).format(solid_name=solid.name, solid_def_name=solid.definition.name,)

    raise DagsterInvalidConfigError(message, evr.errors, failed_config_value)
