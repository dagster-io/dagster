from dagster.config import Field, ScalarUnion, Selector, validate_config
from dagster.utils import merge_dicts


def _get_python_target_configs():
    return {
        'python_file': ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                'relative_path': str,
                'definition': Field(str, is_required=False),
                'location_name': Field(str, is_required=False),
            },
        ),
        'python_module': ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                'module_name': str,
                'definition': Field(str, is_required=False),
                'location_name': Field(str, is_required=False),
            },
        ),
    }


WORKSPACE_CONFIG_SCHEMA = {
    'load_from': [
        Selector(
            merge_dicts(
                _get_python_target_configs(),
                {
                    'python_environment': {
                        'pythonpath': str,
                        'target': Selector(_get_python_target_configs()),
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


def validate_workspace_config(config):
    return validate_config(WORKSPACE_CONFIG_SCHEMA_WITH_LEGACY, config)
