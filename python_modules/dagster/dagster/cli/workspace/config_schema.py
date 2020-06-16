from dagster import check
from dagster.config import Field, ScalarUnion, Selector, validate_config
from dagster.core.errors import DagsterInvalidConfigError
from dagster.utils import merge_dicts


def validate_workspace_config(workspace_config):
    check.dict_param(workspace_config, 'workspace_config')

    return validate_config(WORKSPACE_CONFIG_SCHEMA_WITH_LEGACY, workspace_config)


def ensure_workspace_config(workspace_config, yaml_path):
    check.dict_param(workspace_config, 'workspace_config')
    check.str_param(yaml_path, 'yaml_path')

    validation_result = validate_workspace_config(workspace_config)
    if not validation_result.success:
        raise DagsterInvalidConfigError(
            'Errors while loading workspace config at {}.'.format(yaml_path),
            validation_result.errors,
            workspace_config,
        )
    return validation_result


def _get_target_config():
    return {
        'python_file': ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                'relative_path': str,
                'attribute': Field(str, is_required=False),
                'location_name': Field(str, is_required=False),
            },
        ),
        'python_module': ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                'module_name': str,
                'attribute': Field(str, is_required=False),
                'location_name': Field(str, is_required=False),
            },
        ),
    }


WORKSPACE_CONFIG_SCHEMA = {
    'load_from': [
        Selector(
            merge_dicts(
                _get_target_config(),
                {
                    'python_environment': {
                        'executable_path': str,
                        'target': Selector(_get_target_config()),
                    },
                },
            )
        )
    ],
}

WORKSPACE_CONFIG_SCHEMA_WITH_LEGACY = Selector(
    merge_dicts(
        {
            'repository': {
                'module': Field(str, is_required=False),
                'file': Field(str, is_required=False),
                'fn': Field(str),
            },
        },
        WORKSPACE_CONFIG_SCHEMA,
    )
)
