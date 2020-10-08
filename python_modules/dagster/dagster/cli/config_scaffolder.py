from dagster import PipelineDefinition, check
from dagster.config.config_type import ConfigType, ConfigTypeKind
from dagster.core.definitions import create_environment_type


def scaffold_pipeline_config(pipeline_def, skip_non_required=True, mode=None):
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    check.bool_param(skip_non_required, "skip_non_required")

    env_config_type = create_environment_type(pipeline_def, mode=mode)

    env_dict = {}

    for env_field_name, env_field in env_config_type.fields.items():
        if skip_non_required and not env_field.is_required:
            continue

        # unfortunately we have to treat this special for now
        if env_field_name == "context":
            if skip_non_required and not env_config_type.fields["context"].is_required:
                continue

        env_dict[env_field_name] = scaffold_type(env_field.config_type, skip_non_required)

    return env_dict


def scaffold_type(config_type, skip_non_required=True):
    check.inst_param(config_type, "config_type", ConfigType)
    check.bool_param(skip_non_required, "skip_non_required")

    # Right now selectors and composites have the same
    # scaffolding logic, which might not be wise.
    if ConfigTypeKind.has_fields(config_type.kind):
        default_dict = {}
        for field_name, field in config_type.fields.items():
            if skip_non_required and not field.is_required:
                continue

            default_dict[field_name] = scaffold_type(field.config_type, skip_non_required)
        return default_dict
    elif config_type.kind == ConfigTypeKind.ANY:
        return "AnyType"
    elif config_type.kind == ConfigTypeKind.SCALAR:
        defaults = {"String": "", "Int": 0, "Bool": True}

        return defaults[config_type.given_name]
    elif config_type.kind == ConfigTypeKind.ARRAY:
        return []
    elif config_type.kind == ConfigTypeKind.ENUM:
        return "|".join(sorted(map(lambda v: v.config_value, config_type.enum_values)))
    else:
        check.failed(
            "Do not know how to scaffold {type_name}".format(type_name=config_type.given_name)
        )
