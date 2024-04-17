import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional, Union

from dagster._annotations import experimental, public

from .core.resources_v2 import DbtCliResource
from .errors import DagsterDbtManifestNotPreparedError, DagsterDbtProjectNotFoundError

logger = logging.getLogger("dagster-dbt.artifacts")


@experimental
class DbtArtifacts:
    def __init__(
        self,
        project_dir: Union[Path, str],
        *,
        target_folder: Union[Path, str] = "target",
        prepare_command: List[str] = ["parse", "--quiet"],
        packaged_project_dir: Optional[Union[Path, str]] = None,
    ):
        """A utility class to help manage dbt artifacts in different deployment contexts.

        This class provides a setup to solve for these goals:
        * During development, reload the manifest at run time to pick up any changes.
        * When deploying, expect a manifest that was prepared at build time to reduce start-up time.
        * Handle the scenario when the dbt project is copied in to a directory for packaging.

        Args:
            project_dir (Union[str, Path]):
                The directory of the dbt project.
            target_folder (Union[str, Path]):
                The folder in the project project directory to output artifacts.
                Default: "target"
            prepare_command: The dbt cli command to run to prepare the manifest.json
                Default: ["parse", "--quiet"]
            packaged_project_dir (Union[str, Path]):
                A directory that will contain a copy of the dbt project and the manifest.json
                when the artifacts have been built. The prepare method will handle syncing
                the project_dir to this directory.
                This is useful when the dbt project needs to be part of the python package data
                like when deploying using PEX.
        """
        self.project_dir = Path(project_dir)
        if not self.project_dir.exists():
            raise DagsterDbtProjectNotFoundError(f"project_dir {project_dir} does not exist.")
        self._target_folder = Path(target_folder)
        self._prepare_command = prepare_command
        # this is ok if it doesn't exist, will get created by `prepare`
        self._packaged_project_dir = Path(packaged_project_dir) if packaged_project_dir else None

        if self._should_use_built_artifacts():
            self._manifest_path = self._current_project_dir.joinpath(
                self._target_folder, "manifest.json"
            )
        else:
            self._manifest_path = self._prepare_manifest()

    @public
    @property
    def manifest_path(self) -> Path:
        """The path to the manifest.json, compiling the manifest first if in development or
        ensuring it already exists if not.
        """
        if not self._manifest_path.exists():
            if self._should_use_built_artifacts():
                raise DagsterDbtManifestNotPreparedError(
                    f"Did not find prepared manifest.json at expected path {self._manifest_path}.\n"
                    "If this is an environment that is expected to prepare the manifest at run time, "
                    "set the environment variable DAGSTER_DBT_PARSE_PROJECT_ON_LOAD."
                )
            else:
                raise DagsterDbtManifestNotPreparedError(
                    f"Unexpected state, {self._manifest_path} should have been created when this "
                    "object was initialized."
                )

        return self._manifest_path

    @public
    def prepare(self, *, quiet=False) -> None:
        """A method that can be called as part of the deployment process to handle
        preparing the manifest and if packaged_project_dir is set, handle copying
        the dbt project to that directory.

        Args:
            quiet (bool):
                Disable logging
                Default: False
        """
        level = logging.DEBUG if quiet else logging.INFO
        self._prepare_manifest(level)
        self._handle_package_data(level)
        logger.log(level, "Preparation complete.")

    def _should_use_built_artifacts(self) -> bool:
        # use built artifacts unless
        return not (
            # launched via `dagster dev` cli
            bool(os.getenv("DAGSTER_IS_DEV_CLI"))
            or
            # or if explicitly opted in to loading at runtime
            bool(os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"))
        )

    @property
    def _current_project_dir(self) -> Path:
        if self._should_use_built_artifacts():
            return self._packaged_project_dir if self._packaged_project_dir else self.project_dir

        return self.project_dir

    def _prepare_manifest(self, level: int = logging.DEBUG) -> Path:
        logger.log(
            level, f"Preparing dbt artifacts in {self.project_dir} at {self._target_folder}."
        )
        return (
            DbtCliResource(project_dir=os.fspath(self.project_dir))
            .cli(
                self._prepare_command,
                target_path=self._target_folder,
            )
            .wait()
            .target_path.joinpath("manifest.json")
        )

    def _handle_package_data(self, level: int) -> None:
        if self._packaged_project_dir is None:
            return
        logger.log(level, f"Preparing package data directory {self._packaged_project_dir}.")
        if self._packaged_project_dir.exists():
            logger.log(level, f"Removing existing contents at {self._packaged_project_dir}.")
            shutil.rmtree(self._packaged_project_dir)

        # Determine if the package data dir is within the project dir, and ignore
        # that path if so.
        rel_path = Path(os.path.relpath(self._packaged_project_dir, self.project_dir))
        rel_ignore = ""
        if len(rel_path.parts) > 0 and rel_path.parts[0] != "..":
            rel_ignore = rel_path.parts[0]

        logger.log(level, f"Copying {self.project_dir} to {self._packaged_project_dir}.")
        shutil.copytree(
            src=self.project_dir,
            dst=self._packaged_project_dir,
            ignore=shutil.ignore_patterns(
                "*.git*",
                "*partial_parse.msgpack",
                rel_ignore,
            ),
        )
