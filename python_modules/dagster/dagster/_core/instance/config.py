import os
import warnings
from typing import TYPE_CHECKING, Dict, Optional

from dagster import Array, Bool
from dagster import _check as check
from dagster._config import Field, Permissive, ScalarUnion, Selector, StringSource, validate_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.storage.config import mysql_config, pg_config
from dagster._serdes import class_from_code_pointer
from dagster._utils import merge_dicts
from dagster._utils.yaml_utils import load_yaml_from_globs

if TYPE_CHECKING:
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.scheduler.instigation import TickStatus

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

    if "instance_class" in dagster_config_dict:
        custom_instance_class_data = dagster_config_dict["instance_class"]

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

    if "storage" in dagster_config_dict and (
        "run_storage" in dagster_config_dict
        or "event_log_storage" in dagster_config_dict
        or "schedule_storage" in dagster_config_dict
    ):
        raise DagsterInvalidConfigError(
            (
                "Found config for `storage` which is incompatible with `run_storage`, "
                "`event_log_storage`, and `schedule_storage` config entries."
            ),
            [],
            None,
        )
    elif "storage" in dagster_config_dict:
        if len(dagster_config_dict["storage"]) != 1:
            raise DagsterInvalidConfigError(
                (
                    f"Errors whilst loading dagster storage at {config_filename}, Expected one of:"
                    "['postgres', 'mysql', 'sqlite', 'custom']"
                ),
                [],
                dagster_config_dict["storage"],
            )

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


def storage_config_schema():
    return Field(
        Selector(
            {
                "postgres": Field(pg_config()),
                "mysql": Field(mysql_config()),
                "sqlite": Field({"base_dir": StringSource}),
                "custom": Field(configurable_class_schema()),
            }
        ),
        is_required=False,
    )


def configurable_class_schema():
    return {"module": str, "class": str, "config": Field(Permissive())}


def python_logs_config_schema():
    return Field(
        {
            "managed_python_loggers": Field(Array(str), is_required=False),
            "python_log_level": Field(str, is_required=False),
            "dagster_handler_config": Field(
                {
                    "handlers": Field(dict, is_required=False),
                    "formatters": Field(dict, is_required=False),
                },
                is_required=False,
            ),
        },
        is_required=False,
    )


DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT = 180


def get_default_tick_retention_settings(
    instigator_type: "InstigatorType",
) -> Dict["TickStatus", int]:
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.scheduler.instigation import TickStatus

    if instigator_type == InstigatorType.SCHEDULE:
        return {
            TickStatus.STARTED: -1,
            TickStatus.SKIPPED: -1,
            TickStatus.SUCCESS: -1,
            TickStatus.FAILURE: -1,
        }
    # for sensor
    return {
        TickStatus.STARTED: -1,
        TickStatus.SKIPPED: 7,
        TickStatus.SUCCESS: -1,
        TickStatus.FAILURE: -1,
    }


def _tick_retention_config_schema():
    return Field(
        {
            "purge_after_days": ScalarUnion(
                scalar_type=int,
                non_scalar_schema={
                    "skipped": Field(int, is_required=False),
                    "success": Field(int, is_required=False),
                    "failure": Field(int, is_required=False),
                    "started": Field(int, is_required=False),
                },
            )
        },
        is_required=False,
    )


def retention_config_schema():
    return Field(
        {
            "schedule": _tick_retention_config_schema(),
            "sensor": _tick_retention_config_schema(),
        },
        is_required=False,
    )


def get_tick_retention_settings(
    settings: Optional[Dict],
    default_retention_settings: Dict["TickStatus", int],
) -> Dict["TickStatus", int]:
    if not settings or not settings.get("purge_after_days"):
        return default_retention_settings

    purge_value = settings["purge_after_days"]
    if isinstance(purge_value, int):
        # set a number of days retention value for all tick types
        return {status: purge_value for status, _ in default_retention_settings.items()}

    elif isinstance(purge_value, dict):
        return {
            # override the number of days retention value for tick types that are specified
            status: purge_value.get(status.value.lower(), default_value)
            for status, default_value in default_retention_settings.items()
        }
    else:
        return default_retention_settings


def sensors_daemon_config():
    return Field(
        {
            "use_threads": Field(Bool, is_required=False, default_value=False),
            "num_workers": Field(int, is_required=False),
        },
        is_required=False,
    )


def schedules_daemon_config():
    return Field(
        {
            "use_threads": Field(Bool, is_required=False, default_value=False),
            "num_workers": Field(int, is_required=False),
        },
        is_required=False,
    )


def dagster_instance_config_schema():
    return {
        "local_artifact_storage": config_field_for_configurable_class(),
        "compute_logs": config_field_for_configurable_class(),
        "storage": storage_config_schema(),
        "run_storage": config_field_for_configurable_class(),
        "event_log_storage": config_field_for_configurable_class(),
        "schedule_storage": config_field_for_configurable_class(),
        "scheduler": config_field_for_configurable_class(),
        "run_coordinator": config_field_for_configurable_class(),
        "run_launcher": config_field_for_configurable_class(),
        "telemetry": Field(
            {
                "enabled": Field(Bool, is_required=False),
                "experimental_dagit": Field(Bool, is_required=False, default_value=False),
            },
        ),
        "instance_class": config_field_for_configurable_class(),
        "python_logs": python_logs_config_schema(),
        "run_monitoring": Field(
            {
                "enabled": Field(Bool, is_required=False),
                "start_timeout_seconds": Field(int, is_required=False),
                "max_resume_run_attempts": Field(int, is_required=False),
                "poll_interval_seconds": Field(int, is_required=False),
                "cancellation_thread_poll_interval_seconds": Field(int, is_required=False),
            },
        ),
        "run_retries": Field(
            {
                "enabled": Field(bool, is_required=False, default_value=False),
                "max_retries": Field(int, is_required=False, default_value=0),
            }
        ),
        "code_servers": Field(
            {"local_startup_timeout": Field(int, is_required=False)}, is_required=False
        ),
        "retention": retention_config_schema(),
        "sensors": sensors_daemon_config(),
        "schedules": schedules_daemon_config(),
    }
