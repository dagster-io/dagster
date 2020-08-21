import os

from dagster import Bool, check
from dagster.config import Field, Permissive
from dagster.config.validate import validate_config
from dagster.core.errors import DagsterInvalidConfigError
from dagster.utils import merge_dicts
from dagster.utils.yaml_utils import load_yaml_from_globs

DAGSTER_CONFIG_YAML_FILENAME = "dagster.yaml"


def dagster_instance_config(base_dir, config_filename=DAGSTER_CONFIG_YAML_FILENAME, overrides=None):
    check.str_param(base_dir, "base_dir")
    check.invariant(os.path.isdir(base_dir), "base_dir should be a directory")
    overrides = check.opt_dict_param(overrides, "overrides")
    dagster_config_dict = merge_dicts(
        load_yaml_from_globs(os.path.join(base_dir, config_filename)), overrides
    )
    dagster_config = validate_config(dagster_instance_config_schema(), dagster_config_dict)
    if not dagster_config.success:
        raise DagsterInvalidConfigError(
            "Errors whilst loading dagster instance config at {}.".format(config_filename),
            dagster_config.errors,
            dagster_config_dict,
        )
    return dagster_config.value


def config_field_for_configurable_class():
    return Field({"module": str, "class": str, "config": Field(Permissive())}, is_required=False)


def dagster_instance_config_schema():
    return {
        "local_artifact_storage": config_field_for_configurable_class(),
        "compute_logs": config_field_for_configurable_class(),
        "run_storage": config_field_for_configurable_class(),
        "event_log_storage": config_field_for_configurable_class(),
        "schedule_storage": config_field_for_configurable_class(),
        "scheduler": config_field_for_configurable_class(),
        "run_launcher": config_field_for_configurable_class(),
        "telemetry": Field({"enabled": Field(Bool, default_value=True, is_required=False)}),
        "opt_in": Field({"local_servers": Field(Bool, default_value=False, is_required=False)}),
    }
