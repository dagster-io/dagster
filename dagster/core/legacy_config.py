from dagster import check, config
from .graph import DagsterPipeline

# Do not add new callsites to these functions.
# Only keeping this around in case we need to move the clarify pipeline


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
