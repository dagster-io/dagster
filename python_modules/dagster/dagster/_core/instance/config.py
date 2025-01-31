import logging
import os
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, cast

from dagster import (
    Array,
    Bool,
    String,
    _check as check,
)
from dagster._config import (
    Field,
    IntSource,
    Noneable,
    Permissive,
    ScalarUnion,
    Selector,
    Shape,
    StringSource,
    validate_config,
)
from dagster._config.source import BoolSource
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.storage.config import mysql_config, pg_config
from dagster._record import record
from dagster._serdes import class_from_code_pointer
from dagster._utils.concurrency import get_max_concurrency_limit_value
from dagster._utils.merger import merge_dicts
from dagster._utils.yaml_utils import load_yaml_from_globs

if TYPE_CHECKING:
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.instance import DagsterInstance
    from dagster._core.run_coordinator.queued_run_coordinator import RunQueueConfig
    from dagster._core.scheduler.instigation import TickStatus

DAGSTER_CONFIG_YAML_FILENAME = "dagster.yaml"


def is_dagster_home_set() -> bool:
    return bool(os.getenv("DAGSTER_HOME"))


def dagster_instance_config(
    base_dir: str,
    config_filename: str = DAGSTER_CONFIG_YAML_FILENAME,
    overrides: Optional[Mapping[str, object]] = None,
) -> tuple[Mapping[str, Any], Optional[type["DagsterInstance"]]]:
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

    dagster_config_dict = merge_dicts(load_yaml_from_globs(config_yaml_path) or {}, overrides or {})

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
            type["DagsterInstance"],
            class_from_code_pointer(
                custom_instance_class_data["module"],
                custom_instance_class_data["class"],
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
            "Found config for `run_queue` which is incompatible with `run_coordinator` config"
            " entry.",
            [],
            None,
        )

    if "storage" in dagster_config_dict and (
        "run_storage" in dagster_config_dict
        or "event_log_storage" in dagster_config_dict
        or "schedule_storage" in dagster_config_dict
    ):
        raise DagsterInvalidConfigError(
            "Found config for `storage` which is incompatible with `run_storage`, "
            "`event_log_storage`, and `schedule_storage` config entries.",
            [],
            None,
        )
    elif "storage" in dagster_config_dict:
        if len(dagster_config_dict["storage"]) != 1:
            raise DagsterInvalidConfigError(
                f"Errors whilst loading dagster storage at {config_filename}, Expected one of:"
                "['postgres', 'mysql', 'sqlite', 'custom']",
                [],
                dagster_config_dict["storage"],
            )

    # validate default op concurrency limits
    if "concurrency" in dagster_config_dict:
        validate_concurrency_config(dagster_config_dict)

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


def validate_concurrency_config(dagster_config_dict: Mapping[str, Any]):
    concurrency_config = dagster_config_dict["concurrency"]
    if "pools" in concurrency_config:
        if concurrency_config.get("default_op_concurrency_limit") is not None:
            raise DagsterInvalidConfigError(
                "Found config for `default_op_concurrency_limit` which is incompatible with `pools` config.  Use `pools > default_limit` instead.",
                [],
                None,
            )

        default_concurrency_limit = check.opt_inst(
            pluck_config_value(concurrency_config, ["pools", "default_limit"]), int
        )
        if default_concurrency_limit is not None:
            max_limit = get_max_concurrency_limit_value()
            if default_concurrency_limit < 0 or default_concurrency_limit > max_limit:
                raise DagsterInvalidConfigError(
                    f"Found value `{default_concurrency_limit}` for `pools > default_limit`, "
                    f"Expected value between 0-{max_limit}.",
                    [],
                    None,
                )

        granularity = concurrency_config.get("pools").get("granularity")
        if granularity and granularity not in ["run", "op"]:
            raise DagsterInvalidConfigError(
                f"Found value `{granularity}` for `granularity`, Expected value 'run' or 'op'.",
                [],
                None,
            )

    elif "default_op_concurrency_limit" in concurrency_config:
        default_concurrency_limit = check.opt_inst(
            pluck_config_value(concurrency_config, ["default_op_concurrency_limit"]),
            int,
        )
        if default_concurrency_limit is not None:
            max_limit = get_max_concurrency_limit_value()
            if default_concurrency_limit < 0 or default_concurrency_limit > max_limit:
                raise DagsterInvalidConfigError(
                    f"Found value `{default_concurrency_limit}` for `default_op_concurrency_limit`, "
                    f"Expected value between 0-{max_limit}.",
                    [],
                    None,
                )

    using_concurrency_config = "runs" in concurrency_config or "pools" in concurrency_config
    if using_concurrency_config:
        conflicting_run_queue_fields = [
            ["max_concurrent_runs"],
            ["tag_concurrency_limits"],
            ["block_op_concurrency_limited_runs", "op_concurrency_slot_buffer"],
        ]
        if "run_queue" in dagster_config_dict:
            for field in conflicting_run_queue_fields:
                if pluck_config_value(dagster_config_dict, ["run_queue", *field]) is not None:
                    raise DagsterInvalidConfigError(
                        f"Found config value for `{field}` in `run_queue` which is incompatible with the `concurrency > runs` config",
                        [],
                        None,
                    )

        if "run_coordinator" in dagster_config_dict:
            if (
                pluck_config_value(dagster_config_dict, ["run_coordinator", "class"])
                == "QueuedRunCoordinator"
            ):
                for field in conflicting_run_queue_fields:
                    if (
                        pluck_config_value(
                            dagster_config_dict, ["run_coordinator", "config", *field]
                        )
                        is not None
                    ):
                        raise DagsterInvalidConfigError(
                            f"Found config value for `{field}` in `run_coordinator` which is incompatible with the `concurrency > runs` config",
                            [],
                            None,
                        )


def pluck_config_value(config: Mapping[str, Any], path: Sequence[str]):
    value = config
    for part in path:
        if not isinstance(value, dict):
            return None

        value = value.get(part)
        if value is None:
            return value

    return value


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
                    "filters": Field(dict, is_required=False),
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
    # for sensor / auto-materialize
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
            "auto_materialize": _tick_retention_config_schema(),
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


def backfills_daemon_config() -> Field:
    return Field(
        {
            "use_threads": Field(Bool, is_required=False, default_value=False),
            "num_workers": Field(
                int,
                is_required=False,
                description="How many threads to use to process multiple backfills in parallel",
            ),
        },
        is_required=False,
    )


def sensors_daemon_config() -> Field:
    return Field(
        {
            "use_threads": Field(Bool, is_required=False, default_value=False),
            "num_workers": Field(
                int,
                is_required=False,
                description=(
                    "How many threads to use to process ticks from multiple sensors in parallel"
                ),
            ),
            "num_submit_workers": Field(
                int,
                is_required=False,
                description=(
                    "How many threads to use to submit runs from sensor ticks. Can be used to"
                    " decrease latency when a sensor emits multiple run requests within a single"
                    " tick."
                ),
            ),
        },
        is_required=False,
    )


def schedules_daemon_config() -> Field:
    return Field(
        {
            "use_threads": Field(Bool, is_required=False, default_value=False),
            "num_workers": Field(
                int,
                is_required=False,
                description=(
                    "How many threads to use to process ticks from multiple schedules in parallel"
                ),
            ),
            "num_submit_workers": Field(
                int,
                is_required=False,
                description=(
                    "How many threads to use to submit runs from schedule ticks. Can be used to"
                    " decrease latency when a schedule emits multiple run requests within a single"
                    " tick."
                ),
            ),
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


def get_concurrency_config() -> Field:
    return Field(
        {
            "pools": Field(
                {
                    "default_limit": Field(
                        int,
                        is_required=False,
                        description="The default maximum number of concurrent operations for an unconfigured pool",
                    ),
                    "granularity": Field(
                        str,
                        is_required=False,
                        description="The granularity of the concurrency enforcement of the pool.  One of `run` or `op`.",
                    ),
                    "op_granularity_run_buffer": Field(
                        int,
                        is_required=False,
                        description=(
                            "When the pool scope is set to `op`, this determines the number of runs "
                            "that can be launched with all of its steps blocked waiting for pool slots "
                            "to be freed."
                        ),
                    ),
                },
                is_required=False,
            ),
            "runs": Field(
                {
                    "max_concurrent_runs": Field(
                        int,
                        is_required=False,
                        description=(
                            "The maximum number of runs that are allowed to be in progress at once."
                            " Defaults to 10. Set to -1 to disable the limit. Set to 0 to stop any runs"
                            " from launching. Any other negative values are disallowed."
                        ),
                    ),
                    "tag_concurrency_limits": Field(
                        config=Noneable(
                            Array(
                                Shape(
                                    {
                                        "key": String,
                                        "value": Field(
                                            ScalarUnion(
                                                scalar_type=String,
                                                non_scalar_schema=Shape(
                                                    {"applyLimitPerUniqueValue": Bool}
                                                ),
                                            ),
                                            is_required=False,
                                        ),
                                        "limit": Field(int),
                                    }
                                )
                            )
                        ),
                        is_required=False,
                        description=(
                            "A set of limits that are applied to runs with particular tags. If a value is"
                            " set, the limit is applied to only that key-value pair. If no value is set,"
                            " the limit is applied across all values of that key. If the value is set to a"
                            " dict with `applyLimitPerUniqueValue: true`, the limit will apply to the"
                            " number of unique values for that key."
                        ),
                    ),
                },
                is_required=False,
            ),
            "default_op_concurrency_limit": Field(
                int,
                is_required=False,
                description="[Deprecated] The default maximum number of concurrent operations for an unconfigured concurrency key",
            ),
        }
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
                "cancel_timeout_seconds": Field(int, is_required=False),
                "max_runtime_seconds": Field(int, is_required=False),
                "max_resume_run_attempts": Field(int, is_required=False),
                "poll_interval_seconds": Field(int, is_required=False),
                "cancellation_thread_poll_interval_seconds": Field(int, is_required=False),
                "free_slots_after_run_end_seconds": Field(int, is_required=False),
            },
        ),
        "run_retries": Field(
            {
                "enabled": Field(bool, is_required=False, default_value=False),
                "max_retries": Field(int, is_required=False, default_value=0),
                "retry_on_asset_or_op_failure": Field(
                    bool,
                    is_required=False,
                    default_value=True,
                    description="Whether to retry runs that failed due to assets or ops in the run failing. "
                    "Set this to false if you only want to retry failures that occur "
                    "due to the run worker crashing or unexpectedly terminating, and instead "
                    "rely on op or asset-level retry policies to retry asset or op failures. Setting this "
                    "field to false will only change retry behavior for runs on dagster "
                    "version 1.6.7 or greater.",
                ),
            }
        ),
        "code_servers": Field(
            {
                "local_startup_timeout": Field(int, is_required=False),
                "reload_timeout": Field(int, is_required=False),
                "wait_for_local_processes_on_shutdown": Field(bool, is_required=False),
            },
            is_required=False,
        ),
        "secrets": secrets_loader_config_schema(),
        "retention": retention_config_schema(),
        "backfills": backfills_daemon_config(),
        "sensors": sensors_daemon_config(),
        "schedules": schedules_daemon_config(),
        "auto_materialize": Field(
            {
                "enabled": Field(BoolSource, is_required=False),
                "minimum_interval_seconds": Field(IntSource, is_required=False),
                "run_tags": Field(dict, is_required=False),
                "respect_materialization_data_versions": Field(BoolSource, is_required=False),
                "max_tick_retries": Field(
                    IntSource,
                    default_value=3,
                    is_required=False,
                    description=(
                        "For each auto-materialize tick that raises an error, how many times to retry that tick"
                    ),
                ),
                "use_sensors": Field(BoolSource, is_required=False),
                "use_threads": Field(Bool, is_required=False, default_value=False),
                "num_workers": Field(
                    int,
                    is_required=False,
                    description=(
                        "How many threads to use to process ticks from multiple automation policy sensors in parallel"
                    ),
                ),
            }
        ),
        "concurrency": get_concurrency_config(),
    }


class PoolGranularity(Enum):
    OP = "op"
    RUN = "run"


@record
class PoolConfig:
    pool_granularity: Optional[PoolGranularity]
    default_pool_limit: Optional[int]
    op_granularity_run_buffer: Optional[int]


@record
class ConcurrencyConfig:
    pool_config: PoolConfig
    run_queue_config: Optional["RunQueueConfig"]

    @staticmethod
    def from_concurrency_settings(
        concurrency_settings: Mapping[str, Any],
        run_coordinator_run_queue_config: Optional["RunQueueConfig"],
    ) -> "ConcurrencyConfig":
        from dagster._core.run_coordinator.queued_run_coordinator import RunQueueConfig

        run_settings = concurrency_settings.get("runs", {})
        pool_settings = concurrency_settings.get("pools", {})
        pool_granularity_str = pool_settings.get("granularity")
        if run_coordinator_run_queue_config:
            run_queue_config = RunQueueConfig(
                max_concurrent_runs=run_settings.get(
                    "max_concurrent_runs", run_coordinator_run_queue_config.max_concurrent_runs
                ),
                tag_concurrency_limits=run_settings.get(
                    "tag_concurrency_limits",
                    run_coordinator_run_queue_config.tag_concurrency_limits,
                ),
                max_user_code_failure_retries=run_coordinator_run_queue_config.max_user_code_failure_retries,
                user_code_failure_retry_delay=run_coordinator_run_queue_config.user_code_failure_retry_delay,
                should_block_op_concurrency_limited_runs=bool(pool_settings)
                or run_coordinator_run_queue_config.should_block_op_concurrency_limited_runs,
                op_concurrency_slot_buffer=pool_settings.get(
                    "op_granularity_run_buffer",
                    run_coordinator_run_queue_config.op_concurrency_slot_buffer,
                ),
            )
        else:
            run_queue_config = None

        pool_granularity = PoolGranularity(pool_granularity_str) if pool_granularity_str else None
        if (
            not pool_granularity
            and run_coordinator_run_queue_config
            and run_coordinator_run_queue_config.should_block_op_concurrency_limited_runs
        ):
            # if this was explicitly configured in the run coordinator config, we should default to op granularity
            pool_granularity = PoolGranularity.OP

        default_limit = pool_settings.get("default_limit")
        if default_limit is None:
            default_limit = concurrency_settings.get("default_op_concurrency_limit")

        return ConcurrencyConfig(
            pool_config=PoolConfig(
                pool_granularity=pool_granularity,
                default_pool_limit=default_limit,
                op_granularity_run_buffer=pool_settings.get("op_granularity_run_buffer"),
            ),
            run_queue_config=run_queue_config,
        )
