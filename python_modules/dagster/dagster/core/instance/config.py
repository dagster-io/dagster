import os

from dagster import Bool, Int, check
from dagster.config import Field, Permissive
from dagster.config.field import resolve_to_config_type
from dagster.config.validate import validate_config
from dagster.core.errors import DagsterInvalidConfigError
from dagster.utils import merge_dicts
from dagster.utils.yaml_utils import load_yaml_from_globs

DAGSTER_CONFIG_YAML_FILENAME = "dagster.yaml"


def dagster_instance_config(base_dir, config_filename=DAGSTER_CONFIG_YAML_FILENAME, overrides=None):
    overrides = check.opt_dict_param(overrides, 'overrides')
    dagster_config_dict = merge_dicts(
        load_yaml_from_globs(os.path.join(base_dir, config_filename)), overrides
    )
    dagster_config_type = resolve_to_config_type(define_dagster_config_cls())
    dagster_config = validate_config(dagster_config_type, dagster_config_dict)
    if not dagster_config.success:
        raise DagsterInvalidConfigError(
            'Errors whilst loading dagster instance config at {}.'.format(config_filename),
            dagster_config.errors,
            dagster_config_dict,
        )
    return dagster_config.value


def config_field_for_configurable_class():
    return Field({'module': str, 'class': str, 'config': Field(Permissive())}, is_required=False)


def define_dagster_config_cls():
    return {
        'local_artifact_storage': config_field_for_configurable_class(),
        'compute_logs': config_field_for_configurable_class(),
        'run_storage': config_field_for_configurable_class(),
        'event_log_storage': config_field_for_configurable_class(),
        'schedule_storage': config_field_for_configurable_class(),
        'scheduler': config_field_for_configurable_class(),
        'run_launcher': config_field_for_configurable_class(),
        'dagit': Field(
            {
                'execution_manager': Field(
                    {
                        'disabled': Field(Bool, is_required=False),
                        'max_concurrent_runs': Field(Int, is_required=False),
                    },
                    is_required=False,
                ),
            },
            is_required=False,
        ),
        'telemetry': Field({'enabled': Field(Bool, default_value=False, is_required=False)}),
    }
