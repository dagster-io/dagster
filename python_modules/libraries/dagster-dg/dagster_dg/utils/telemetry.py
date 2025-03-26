import datetime
import sys
from collections.abc import Mapping
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union, overload

import click
from dagster_shared.telemetry import (
    TelemetrySettings,
    get_or_set_instance_id,
    get_telemetry_enabled_from_dagster_yaml,
    log_telemetry_action as shared_log_telemetry_action,
)
from dagster_shared.utils.config import does_dg_config_file_exist
from typing_extensions import ParamSpec

from dagster_dg.config import DgCliConfig, load_dg_user_file_config
from dagster_dg.version import __version__


def get_telemetry_enabled_for_cli() -> bool:
    """Returns whether telemetry is enabled in the CLI, e.g.
    if it is disabled through the telemetry.enabled setting in
    the config file.
    """
    user_config = load_dg_user_file_config() if does_dg_config_file_exist() else None
    if not user_config:
        return True
    config = DgCliConfig.from_raw(user_config)
    if not config.telemetry_enabled:
        return False
    return True


def get_telemetry_settings_for_cli() -> TelemetrySettings:
    enabled = get_telemetry_enabled_for_cli() and get_telemetry_enabled_from_dagster_yaml()
    return TelemetrySettings(
        dagster_telemetry_enabled=enabled,
        instance_id=get_or_set_instance_id() if enabled else None,
        run_storage_id=None,
    )


def log_telemetry_action(
    action: str,
    client_time: Optional[datetime.datetime] = None,
    elapsed_time: Optional[datetime.timedelta] = None,
    metadata: Optional[Mapping[str, str]] = None,
) -> None:
    return shared_log_telemetry_action(
        lambda: get_telemetry_settings_for_cli(),
        action,
        client_time,
        elapsed_time,
        {"dagster_dg_version": __version__, **(metadata or {})},
    )


P = ParamSpec("P")
T = TypeVar("T")
T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])


@overload
def cli_telemetry_wrapper(target_fn: T_Callable) -> T_Callable: ...


@overload
def cli_telemetry_wrapper(
    *,
    metadata: Optional[Mapping[str, str]],
) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


def cli_telemetry_wrapper(
    target_fn: Optional[T_Callable] = None, *, metadata: Optional[Mapping[str, str]] = None
) -> Union[T_Callable, Callable[[Callable[P, T]], Callable[P, T]]]:
    """Wrapper around functions that are logged. Will log the function_name, client_time, and
    elapsed_time, and success.
    """
    if target_fn is not None:
        return _cli_telemetry_wrapper(target_fn)

    def _wraps(f: Callable[P, T]) -> Callable[P, T]:
        return _cli_telemetry_wrapper(f, metadata)

    return _wraps


def _cli_telemetry_wrapper(
    f: Callable[P, T], metadata: Optional[Mapping[str, str]] = None
) -> Callable[P, T]:
    if isinstance(f, click.Command):
        raise Exception(
            "@dg_telemetry_wrapper should be placed on the command function, below the @click.command decorator"
        )

    @wraps(f)
    def wrap(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = datetime.datetime.now()
        log_telemetry_action(
            action=f.__name__ + "_started",
            client_time=start_time,
            metadata=metadata,
        )
        exception_name = None
        try:
            result = f(*args, **kwargs)
        except Exception as e:
            if not isinstance(e, click.exceptions.Exit) or e.exit_code != 0:
                exception_name, _, _ = sys.exc_info()
            raise
        finally:
            end_time = datetime.datetime.now()

            log_telemetry_action(
                action=f.__name__ + "_ended",
                client_time=end_time,
                elapsed_time=end_time - start_time,
                metadata={
                    "command_success": str(exception_name is None),
                    "exception": str(exception_name),
                    **(metadata or {}),
                },
            )
        return result

    setattr(wrap, "__has_cli_telemetry_wrapper", True)
    return wrap
