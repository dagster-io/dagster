# Do not add new callsites to these functions.
# Only keeping this around in case we need to move the clarify pipeline

# This is the legacy format for specifying inputs.

# Keeping this around because the clarify pipeline is still using this as we finalize
# the real config inputs. We don't want to thrash that pipeline until we finalize
# the input api

# input_arg_dicts: {string : { string: string } }

# A dictionary of dictionaries. The first level is indexed by input *name*. Put an entry for each
# input you want to specify. Each one of inputs in turn has an argument dictionary, which is just
# a set of key value pairs, represented by a bare python dictionary:

# So for example a solid that takes two csv inputs would have the input_arg_dicts:

# {
#     "csv_one" : { "path" : "path/to/csv_one.csv},
#     "csv_two" : { "path" : "path/to/csv_two.csv},
# }

from dagster import check, config
from .definitions import SolidDefinition
from .graph import DagsterPipeline


def create_pipeline_env_from_arg_dicts(pipeline, arg_dicts):
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.dict_param(arg_dicts, 'arg_dicts', key_type=str, value_type=dict)

    inputs = {}
    input_to_source_type = {}

    for solid in pipeline.solids:
        for input_def in solid.inputs:
            if input_def.sources:
                input_to_source_type[input_def.name] = input_def.sources[0].source_type

    inputs = []
    for input_name, arg_dict in arg_dicts.items():
        if input_name in input_to_source_type:
            inputs.append(
                config.Input(
                    input_name=input_name,
                    source=input_to_source_type[input_name],
                    args=arg_dict,
                )
            )

    return config.Environment(inputs=inputs)


def create_single_solid_env_from_arg_dicts(solid, arg_dicts):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.dict_param(arg_dicts, 'arg_dicts', key_type=str, value_type=dict)

    input_to_source_type = {}
    for input_def in solid.inputs:
        check.invariant(len(input_def.sources) == 1)
        input_to_source_type[input_def.name] = input_def.sources[0].source_type

    inputs = []

    for input_name, arg_dict in arg_dicts.items():
        inputs.append(
            config.Input(
                input_name=input_name,
                source=input_to_source_type[input_name],
                args=arg_dict,
            )
        )

    return config.Environment(inputs=inputs)
