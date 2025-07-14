import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from dagster import Component, Resolvable
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.test_utils import environ
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import ResolvedAssetKey


def airlift_root() -> Path:
    return Path(__file__).parent.parent.parent


def remove_airflow_home_remnants(airflow_home: Path) -> None:
    logs_path = airflow_home / "logs"
    cfg_path = airflow_home / "airflow.cfg"
    db_path = airflow_home / "airflow.db"
    proxied_state_path = airflow_home / "airflow_dags" / "proxied_state"

    subprocess.check_output(
        ["rm", "-rf", str(logs_path), str(cfg_path), str(db_path), str(proxied_state_path)]
    )


def airflow_cfg_script_path() -> Path:
    return airlift_root() / "scripts" / "airflow_setup.sh"


def chmod_script(script_path: Path) -> None:
    subprocess.check_output(["chmod", "+x", str(script_path)])


@contextmanager
def configured_airflow_home(airflow_home: Path) -> Generator[None, None, None]:
    path_to_dags = airflow_home / "airflow_dags"
    with environ({"AIRFLOW_HOME": str(airflow_home)}):
        try:
            # Start by removing old cruft if it exists
            remove_airflow_home_remnants(airflow_home)
            # Scaffold the airflow configuration file.
            chmod_script(airflow_cfg_script_path())
            subprocess.run(
                [str(airflow_cfg_script_path()), str(path_to_dags), str(airflow_home)], check=False
            )
            yield
        finally:
            # Clean up after ourselves.
            remove_airflow_home_remnants(airflow_home)


def asset_spec(asset_str: str, defs: Definitions) -> Optional[AssetSpec]:
    """Get the spec of an asset from the definitions by its string representation."""
    return next(
        iter(
            spec
            for spec in defs.resolve_all_asset_specs()
            if spec.key.to_user_string() == asset_str
        ),
        None,
    )


def get_job_from_defs(
    name: str, defs: Definitions
) -> Optional[Union[JobDefinition, UnresolvedAssetJobDefinition]]:
    """Get the job from the definitions by its name."""
    return next(
        iter(job for job in (defs.jobs or []) if job.name == name),
        None,
    )


@dataclass
class BasicAssetComponent(Component, Resolvable):
    key: ResolvedAssetKey

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self.key)
        def asset_def():
            pass

        return Definitions(assets=[asset_def])
