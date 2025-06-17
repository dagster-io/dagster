import datetime
import os
from functools import cached_property
from typing import Optional

from dagster_dg_core.context import DgContext
from dagster_dg_core.utils.warnings import emit_warning
from dagster_shared.libraries import DagsterPyPiAccessError, get_published_pypi_versions
from dagster_shared.record import record
from packaging.version import Version

from create_dagster.version import __version__

CREATE_DAGSTER_UPDATE_CHECK_ENABLED_ENV_VAR = "DAGSTER_DG_UPDATE_CHECK_ENABLED"


@record
class _PyPiVersionInfo:
    timestamp: float
    raw_versions: list[str]

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp)

    @cached_property
    def versions(self) -> list[Version]:
        return sorted(Version(v) for v in self.raw_versions)


def check_create_dagster_up_to_date(context: DgContext) -> None:
    if not _create_dagster_update_check_enabled(context):
        return

    version_info = _get_create_dagster_pypi_version_info(context)
    if version_info is None:  # Nothing cached and network error occurred
        return None

    current_version = Version(__version__)
    latest_version = version_info.versions[-1]
    if current_version < latest_version:
        emit_warning(
            "create_dagster_outdated",
            f"""
                There is a new version of `create-dagster` available:

                    Latest version: {latest_version}
                    Current version: {current_version}

                Update your create-dagster installation to keep up to date:

                    [uv tool run]      $ uvx -U create-dagster
                    [uv tool install]  $ uv tool upgrade create-dagster
                    [uv local]         $ uv sync --upgrade create-dagster
                    [pip]              $ pip install --upgrade create-dagster
            """,
            suppress_warnings=[],
        )


def _create_dagster_update_check_enabled(context: DgContext) -> bool:
    return (
        bool(int(os.getenv(CREATE_DAGSTER_UPDATE_CHECK_ENABLED_ENV_VAR, "1")))
        and "create_dagster_outdated" not in context.config.cli.suppress_warnings
    )


def _get_create_dagster_pypi_version_info(context: DgContext) -> Optional[_PyPiVersionInfo]:
    if context.config.cli.verbose:
        context.log.info("Checking for the latest version of `create-dagster` on PyPI.")
    try:
        published_versions = get_published_pypi_versions("create-dagster")
        version_info = _PyPiVersionInfo(
            raw_versions=[str(v) for v in published_versions],
            timestamp=datetime.datetime.now().timestamp(),
        )
    except DagsterPyPiAccessError as e:
        emit_warning(
            "create_dagster_outdated",
            f"""
                There was an error checking for the latest version of `create-dagster` on PyPI. Please check your
                internet connection and try again.

                Error: {e}
                """,
            suppress_warnings=[],
        )
        version_info = None
    return version_info
