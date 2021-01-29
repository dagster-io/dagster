import os
import warnings

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

    config_yaml_path = os.path.join(base_dir, config_filename)

    if not os.path.exists(config_yaml_path):
        warnings.warn(
            (
                "The dagster instance configuration file ({config_filename}) is not present at "
                "{base_dir}. Dagster uses this file to know where and how to store "
                "local artifacts, information about past runs, and structured events.\n"
                "If nothing is specified, Dagster will store this information "
                "in the local filesystem in the {base_dir} directory."
            ).format(config_filename=config_filename, base_dir=base_dir)
        )

    dagster_config_dict = merge_dicts(load_yaml_from_globs(config_yaml_path), overrides)
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
        "run_coordinator": config_field_for_configurable_class(),
        "run_launcher": config_field_for_configurable_class(),
        "telemetry": Field({"enabled": Field(Bool, is_required=False)}),
        "sensor_settings": Field({"interval_seconds": Field(int, is_required=False)}),
    }
