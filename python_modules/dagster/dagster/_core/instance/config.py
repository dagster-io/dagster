import logging
import os
from typing import TYPE_CHECKING, Any, Mapping, Optional, Tuple, Type, cast

from dagster import (
    Array,
    Bool,
    _check as check,
)
from dagster._config import Field, Permissive, ScalarUnion, Selector, StringSource, validate_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.storage.config import mysql_config, pg_config
from dagster._serdes import class_from_code_pointer
from dagster._utils.merger import merge_dicts
from dagster._utils.yaml_utils import load_yaml_from_globs

if TYPE_CHECKING:
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.instance import DagsterInstance
    from dagster._core.scheduler.instigation import TickStatus

DAGSTER_CONFIG_YAML_FILENAME = "dagster.yaml"


def is_dagster_home_set() -> bool:
    return bool(os.getenv("DAGSTER_HOME"))


def dagster_instance_config(
    base_dir: str,
    config_filename: str = DAGSTER_CONFIG_YAML_FILENAME,
    overrides: Optional[Mapping[str, object]] = None,
) -> Tuple[Mapping[str, Any], Optional[Type["DagsterInstance"]]]:
    check.str_param(base_dir, "base_dir")
    check.invariant(os.path.isdir(base_dir), "base_dir should be a directory")
    overrides = check.opt_mapping_param(overrides, "overrides")

    config_yaml_path = os.path.join(base_dir, config_filename)

    if not os.path.exists(config_yaml_path) and is_dagster_home_set():
        logging.getLogger("dagster").warning(
            f"No dagster instance configuration file ({config_filename}) found at {base_dir}."
            f" Defaulting to loading and storing all metadata with {base_dir}. If this is the"
            f" desired behavior, create an empty {config_filename} file in {base_dir}."
        )

    dagster_config_dict = merge_dicts(load_yaml_from_globs(config_yaml_path) or {}, overrides)

    if "instance_class" in dagster_config_dict:
        custom_instance_class_data = dagster_config_dict["instance_class"]

        validate_custom_config = validate_config(
            configurable_class_schema(),
            custom_instance_class_data,
        )
        if not validate_custom_config.success:
            raise DagsterInvalidConfigError(
                f"Errors whilst loading dagster custom class config at {config_filename}",
                validate_custom_config.errors,
                custom_instance_class_data,
            )

        custom_instance_class = cast(
            Type["DagsterInstance"],
            class_from_code_pointer(
                custom_instance_class_data["module"], custom_instance_class_data["class"]
            ),
        )

        schema: Mapping[str, Field]
        if hasattr(custom_instance_class, "config_schema"):
            schema = merge_dicts(
                dagster_instance_config_schema(),
                custom_instance_class.config_schema(),  # type: ignore
            )
        else:
            schema = dagster_instance_config_schema()
    else:
        custom_instance_class = None
        schema = dagster_instance_config_schema()

    if "run_queue" in dagster_config_dict and "run_coordinator" in dagster_config_dict:
        raise DagsterInvalidConfigError(
            (
                "Found config for `run_queue` which is incompatible with `run_coordinator` config"
                " entry."
            ),
            [],
            None,
        )

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
            f"Errors whilst loading dagster instance config at {config_filename}.",
            dagster_config.errors,
            dagster_config_dict,
        )

    return (check.not_none(dagster_config.value), custom_instance_class)


def config_field_for_configurable_class() -> Field:
    return Field(configurable_class_schema(), is_required=False)


def run_queue_config_schema() -> Field:
    from dagster._core.run_coordinator.queued_run_coordinator import QueuedRunCoordinator

    return Field(
        QueuedRunCoordinator.config_type(),
        is_required=False,
    )


def storage_config_schema() -> Field:
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


def configurable_class_schema() -> Mapping[str, Any]:
    return {"module": str, "class": str, "config": Field(Permissive())}


def python_logs_config_schema() -> Field:
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
) -> Mapping["TickStatus", int]:
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


def _tick_retention_config_schema() -> Field:
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


def retention_config_schema() -> Field:
    return Field(
        {
            "schedule": _tick_retention_config_schema(),
            "sensor": _tick_retention_config_schema(),
        },
        is_required=False,
    )


def get_tick_retention_settings(
    settings: Optional[Mapping[str, Any]],
    default_retention_settings: Mapping["TickStatus", int],
) -> Mapping["TickStatus", int]:
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


def sensors_daemon_config() -> Field:
    return Field(
        {
            "use_threads": Field(Bool, is_required=False, default_value=False),
            "num_workers": Field(int, is_required=False),
        },
        is_required=False,
    )


def schedules_daemon_config() -> Field:
    return Field(
        {
            "use_threads": Field(Bool, is_required=False, default_value=False),
            "num_workers": Field(int, is_required=False),
        },
        is_required=False,
    )


def secrets_loader_config_schema() -> Field:
    return Field(
        Selector(
            {
                # Space to add additional built-in secrets loaders in the future, for now
                # only custom
                "custom": Field(configurable_class_schema()),
            }
        ),
        is_required=False,
    )


def dagster_instance_config_schema() -> Mapping[str, Field]:
    return {
        "local_artifact_storage": config_field_for_configurable_class(),
        "compute_logs": config_field_for_configurable_class(),
        "storage": storage_config_schema(),
        "run_queue": run_queue_config_schema(),
        "run_storage": config_field_for_configurable_class(),
        "event_log_storage": config_field_for_configurable_class(),
        "schedule_storage": config_field_for_configurable_class(),
        "scheduler": config_field_for_configurable_class(),
        "run_coordinator": config_field_for_configurable_class(),
        "run_launcher": config_field_for_configurable_class(),
        "telemetry": Field(
            {"enabled": Field(Bool, is_required=False)},
        ),
        "nux": Field(
            {"enabled": Field(Bool, is_required=False)},
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
            {
                "local_startup_timeout": Field(int, is_required=False),
                "wait_for_local_processes_on_shutdown": Field(bool, is_required=False),
            },
            is_required=False,
        ),
        "secrets": secrets_loader_config_schema(),
        "retention": retention_config_schema(),
        "sensors": sensors_daemon_config(),
        "schedules": schedules_daemon_config(),
        "auto_materialize": Field(
            {
                "enabled": Field(Bool, is_required=False),
                "minimum_interval_seconds": Field(int, is_required=False),
                "run_tags": Field(dict, is_required=False),
            }
        ),
    }
