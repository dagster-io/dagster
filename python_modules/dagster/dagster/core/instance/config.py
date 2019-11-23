import os

from dagster import check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.types import Field, PermissiveDict, String
from dagster.core.types.evaluator import evaluate_config
from dagster.utils import merge_dicts
from dagster.utils.yaml_utils import load_yaml_from_globs

DAGSTER_CONFIG_YAML_FILENAME = "dagster.yaml"


def dagster_instance_config(base_dir, config_filename=DAGSTER_CONFIG_YAML_FILENAME, overrides=None):
    overrides = check.opt_dict_param(overrides, 'overrides')
    dagster_config_dict = merge_dicts(
        load_yaml_from_globs(os.path.join(base_dir, config_filename)), overrides
    )
    dagster_config_type = define_dagster_config_cls().inst()
    dagster_config = evaluate_config(dagster_config_type, dagster_config_dict)
    if not dagster_config.success:
        raise DagsterInvalidConfigError(None, dagster_config.errors, dagster_config_dict)
    return dagster_config.value


def config_field_for_configurable_class(name, **field_opts):
    return Field(
        SystemNamedDict(
            name,
            {'module': Field(String), 'class': Field(String), 'config': Field(PermissiveDict())},
        ),
        **field_opts
    )


def define_dagster_config_cls():
    return SystemNamedDict(
        'DagsterInstanceConfig',
        {
            'local_artifact_storage': config_field_for_configurable_class(
                'DagsterInstanceLocalArtifactStorageConfig', is_optional=True
            ),
            'compute_logs': config_field_for_configurable_class(
                'DagsterInstanceComputeLogsConfig', is_optional=True
            ),
            'run_storage': config_field_for_configurable_class(
                'DagsterInstanceRunStorageConfig', is_optional=True
            ),
            'event_log_storage': config_field_for_configurable_class(
                'DagsterInstanceEventLogStorageConfig', is_optional=True
            ),
            'run_launcher': config_field_for_configurable_class(
                'DagsterInstanceRunLauncherConfig', is_optional=True
            ),
        },
    )
