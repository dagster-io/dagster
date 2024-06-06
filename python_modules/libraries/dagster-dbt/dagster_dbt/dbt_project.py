import logging
import os
from pathlib import Path
from typing import Optional, Sequence, Union

import yaml
from dagster._annotations import experimental
from dagster._model import IHaveNew, dagster_model_custom
from dagster._utils import run_with_concurrent_update_guard

from .errors import (
    DagsterDbtManifestNotFoundError,
    DagsterDbtProjectNotFoundError,
    DagsterDbtProjectYmlFileNotFoundError,
)

logger = logging.getLogger("dagster-dbt.artifacts")


def using_dagster_dev() -> bool:
    return bool(os.getenv("DAGSTER_IS_DEV_CLI"))


@experimental
class DbtManifestPreparer:
    """A dbt manifest represented by DbtProject."""

    def on_load(self, project: "DbtProject") -> None:
        """Invoked when DbtProject is instantiated with this preparer."""

    def prepare(self, project: "DbtProject") -> None:
        """Called explictly to prepare the manifest for this the project."""

    def using_dagster_dev(self) -> bool:
        return using_dagster_dev()

    def parse_on_load_opt_in(self) -> bool:
        return bool(os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"))


@experimental
class DagsterDbtManifestPreparer(DbtManifestPreparer):
    def __init__(
        self,
        generate_cli_args: Optional[Sequence[str]] = None,
    ):
        """The default DbtManifestPreparer, this handler provides an experience of:
            * During development, reload the manifest at run time to pick up any changes.
            * When deploying, expect a manifest that was created at build time to reduce start-up time.

        Args:
            generate_cli_args (Sequence[str]):
                The arguments to pass to the dbt cli to generate a manifest.json.
                Default: ["parse", "--quiet"]
        """
        self._generate_cli_args = generate_cli_args or ["parse", "--quiet"]

    def on_load(self, project: "DbtProject"):
        if self.using_dagster_dev() or self.parse_on_load_opt_in():
            self.prepare(project)
            if not project.manifest_path.exists():
                raise DagsterDbtManifestNotFoundError(
                    f"Did not find manifest.json at expected path {project.manifest_path} "
                    f"after running '{self.prepare.__qualname__}'. Ensure the implementation respects "
                    "all DbtProject properties."
                )

    def prepare(self, project: "DbtProject") -> None:
        # guard against multiple Dagster processes trying to update this at the same time
        if project.has_uninstalled_deps:
            run_with_concurrent_update_guard(
                project.project_dir.joinpath("package-lock.yml"),
                self._prepare_packages,
                project=project,
            )

        run_with_concurrent_update_guard(
            project.manifest_path,
            self._prepare_manifest,
            project=project,
        )

    def _prepare_packages(self, project: "DbtProject") -> None:
        from .core.resources_v2 import DbtCliResource

        (
            DbtCliResource(project_dir=project)
            .cli(["deps", "--quiet"], target_path=project.target_path)
            .wait()
        )

    def _prepare_manifest(self, project: "DbtProject") -> None:
        from .core.resources_v2 import DbtCliResource

        (
            DbtCliResource(project_dir=project)
            .cli(
                self._generate_cli_args,
                target_path=project.target_path,
            )
            .wait()
        )


@experimental
@dagster_model_custom
class DbtProject(IHaveNew):
    """Representation of a dbt project and related settings that assist with managing manifest.json preparation.

    By default, using this helps achieve a setup where:
    * during development, reload the manifest at run time to pick up any changes.
    * when deployed, expect a manifest that was created at build time to reduce start-up time.

    The cli ``dagster-dbt project prepare-for-deployment`` can be used as part of the deployment process to
    handle manifest.json preparation.

    This object can be passed directly to :py:class:`~dagster_dbt.DbtCliResource`.

    Args:
        project_dir (Union[str, Path]):
            The directory of the dbt project.
        target_path (Union[str, Path]):
            The path, relative to the project directory, to output artifacts.
            Default: "target"
        target (Optional[str]):
            The target from your dbt `profiles.yml` to use for execution, if it should be explicitly set.
        packaged_project_dir (Optional[Union[str, Path]]):
            A directory that will contain a copy of the dbt project and the manifest.json
            when the artifacts have been built. The prepare method will handle syncing
            the project_path to this directory.
            This is useful when the dbt project needs to be part of the python package data
            like when deploying using PEX.
        state_path (Optional[Union[str, Path]]):
            The path, relative to the project directory, to reference artifacts from another run.
        manifest_preparer (Optional[DbtManifestPreparer]):
            A object for ensuring that manifest.json is in the right state at
            the right times.
            Default: DagsterDbtManifestPreparer

    Examples:
        Creating a DbtProject with by referencing the dbt project directory:

        .. code-block:: python

            from pathlib import Path

            from dagster_dbt import DbtProject

            my_project = DbtProject(project_dir=Path("path/to/dbt_project"))

        Creating a DbtProject that changes target based on environment variables and uses manged state artifacts:

        .. code-block:: python

            import os
            from pathlib import Path
            from dagster_dbt import DbtProject


            def get_env():
                if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
                    return "BRANCH"
                if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "prod":
                    return "PROD"
                return "LOCAL"


            dbt_project = DbtProject(
                project_dir=Path('path/to/dbt_project'),
                state_path="target/managed_state",
                target=get_env(),
            )

    """

    project_dir: Path
    target_path: Path
    target: Optional[str]
    manifest_path: Path
    packaged_project_dir: Optional[Path]
    state_path: Optional[Path]
    has_uninstalled_deps: bool
    manifest_preparer: DbtManifestPreparer

    def __new__(
        cls,
        project_dir: Union[Path, str],
        *,
        target_path: Union[Path, str] = Path("target"),
        target: Optional[str] = None,
        packaged_project_dir: Optional[Union[Path, str]] = None,
        state_path: Optional[Union[Path, str]] = None,
        manifest_preparer: DbtManifestPreparer = DagsterDbtManifestPreparer(),
    ):
        project_dir = Path(project_dir)
        if not project_dir.exists():
            raise DagsterDbtProjectNotFoundError(f"project_dir {project_dir} does not exist.")

        packaged_project_dir = Path(packaged_project_dir) if packaged_project_dir else None
        if not using_dagster_dev() and packaged_project_dir and packaged_project_dir.exists():
            project_dir = packaged_project_dir

        manifest_path = project_dir.joinpath(target_path, "manifest.json")

        dependencies_path = project_dir.joinpath("dependencies.yml")
        packages_path = project_dir.joinpath("packages.yml")

        dbt_project_yml_path = project_dir.joinpath("dbt_project.yml")
        if not dbt_project_yml_path.exists():
            raise DagsterDbtProjectYmlFileNotFoundError(
                f"Did not find dbt_project.yml at expected path {dbt_project_yml_path}. "
                f"Ensure the specified project directory respects all dbt project requirements."
            )
        with open(project_dir.joinpath("dbt_project.yml")) as file:
            dbt_project_yml = yaml.safe_load(file)
        packages_install_path = project_dir.joinpath(
            dbt_project_yml.get("packages-install-path", "dbt_packages")
        )

        has_uninstalled_deps = (
            dependencies_path.exists() or packages_path.exists()
        ) and not packages_install_path.exists()

        val = super().__new__(
            cls,
            project_dir=project_dir,
            target_path=target_path,
            target=target,
            manifest_path=manifest_path,
            state_path=project_dir.joinpath(state_path) if state_path else None,
            packaged_project_dir=packaged_project_dir,
            has_uninstalled_deps=has_uninstalled_deps,
            manifest_preparer=manifest_preparer,
        )
        if manifest_preparer:
            manifest_preparer.on_load(val)
        return val
