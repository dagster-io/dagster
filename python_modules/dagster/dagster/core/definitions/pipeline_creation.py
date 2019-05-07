from dagster.core.types.runtime import ALL_RUNTIME_BUILTINS


def construct_runtime_type_dictionary(solid_defs):
    type_dict = {t.name: t for t in ALL_RUNTIME_BUILTINS}
    for solid_def in solid_defs:
        for input_def in solid_def.input_dict.values():
            type_dict[input_def.runtime_type.name] = input_def.runtime_type
            for inner_type in input_def.runtime_type.inner_types:
                type_dict[inner_type.name] = inner_type

        for output_def in solid_def.output_dict.values():
            type_dict[output_def.runtime_type.name] = output_def.runtime_type
            for inner_type in output_def.runtime_type.inner_types:
                type_dict[inner_type.name] = inner_type

    return type_dict
