import check

from .solid_defs import (Solid, SolidExecutionContext, SolidInputDefinition)


def materialize_input(context, input_definition, arg_dict):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(input_definition, 'input_defintion', SolidInputDefinition)
    check.dict_param(arg_dict, 'arg_dict')

    ## INTO USER SPACE
    materialized = input_definition.input_fn(**arg_dict)

    return materialized


def execute_core_transform(context, solid, materialized_inputs):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(materialized_inputs, 'materialized_inputs', key_type=str)

    ## INTO USER SPACE
    materialized_output = solid.transform_fn(**materialized_inputs)

    return materialized_output


def execute_solid(context, solid, input_arg_dicts, output_type, output_arg_dict):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'materialized_inputs', key_type=str, value_type=dict)
    check.str_param(output_type, 'output_type')
    check.dict_param(output_arg_dict, 'output_arg_dict')

    materialized_inputs = {}

    for input_name, arg_dict in input_arg_dicts.items():
        input_def = solid.input_def_named(input_name)
        ## INTO USER SPACE
        materialized_input = materialize_input(context, input_def, arg_dict)
        materialized_inputs[input_name] = materialized_input

    materialized_output = execute_core_transform(context, solid, materialized_inputs)

    output_type_def = solid.output_type_def_named(output_type)

    ## INTO USER SPACE
    output_type_def.output_fn(materialized_output)
