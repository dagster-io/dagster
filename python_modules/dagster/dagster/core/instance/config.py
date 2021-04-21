import os
import warnings

from dagster import Bool, check
from dagster.config import Field, Permissive
from dagster.config.validate import validate_config
from dagster.core.errors import DagsterInvalidConfigError
from dagster.serdes import class_from_code_pointer
from dagster.utils import merge_dicts
from dagster.utils.yaml_utils import load_yaml_from_globs

DAGSTER_CONFIG_YAML_FILENAME = "dagster.yaml"


def is_dagster_home_set():
    return bool(os.getenv("DAGSTER_HOME"))


def dagster_instance_config(
    base_dir,
    config_filename=DAGSTER_CONFIG_YAML_FILENAME,
    overrides=None,
):
    check.str_param(base_dir, "base_dir")
    check.invariant(os.path.isdir(base_dir), "base_dir should be a directory")
    overrides = check.opt_dict_param(overrides, "overrides")

    config_yaml_path = os.path.join(base_dir, config_filename)

    if not os.path.exists(config_yaml_path) and is_dagster_home_set():
        warnings.warn(
            f"No dagster instance configuration file ({config_filename}) found at "
            f"{base_dir}. Defaulting to loading and storing all metadata with {base_dir}. "
            f"If this is the desired behavior, create an empty {config_filename} file in {base_dir}."
        )

    dagster_config_dict = merge_dicts(load_yaml_from_globs(config_yaml_path), overrides)

    if "custom_instance_class" in dagster_config_dict:
        custom_instance_class_data = dagster_config_dict["custom_instance_class"]

        validate_custom_config = validate_config(
            configurable_class_schema(),
            custom_instance_class_data,
        )
        if not validate_custom_config.success:
            raise DagsterInvalidConfigError(
                "Errors whilst loading dagster custom class config at {}".format(config_filename),
                validate_custom_config.errors,
                custom_instance_class_data,
            )

        custom_instance_class = class_from_code_pointer(
            custom_instance_class_data["module"], custom_instance_class_data["class"]
        )

        schema = merge_dicts(
            dagster_instance_config_schema(), custom_instance_class.config_schema()
        )
    else:
        custom_instance_class = None
        schema = dagster_instance_config_schema()

    dagster_config = validate_config(schema, dagster_config_dict)
    if not dagster_config.success:
        raise DagsterInvalidConfigError(
            "Errors whilst loading dagster instance config at {}.".format(config_filename),
            dagster_config.errors,
            dagster_config_dict,
        )

    return (dagster_config.value, custom_instance_class)


def config_field_for_configurable_class():
    return Field(configurable_class_schema(), is_required=False)


def configurable_class_schema():
    return {"module": str, "class": str, "config": Field(Permissive())}


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
        "custom_instance_class": config_field_for_configurable_class(),
    }
