import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Sequence, Union

from dagster._annotations import experimental, public

from .errors import DagsterDbtManifestNotPreparedError, DagsterDbtProjectNotFoundError

logger = logging.getLogger("dagster-dbt.artifacts")


@experimental
class DbtProject:
    def __init__(
        self,
        project_dir: Union[Path, str],
        *,
        target_folder: Union[Path, str] = "target",
        generate_artifacts_args: Sequence[str] = ["parse", "--quiet"],
        packaged_project_dir: Optional[Union[Path, str]] = None,
        state_artifacts_folder: Optional[Union[str, Path]] = None,
    ):
        """Manages a dbt project that will be used in Dagster.

        This class handles some common behaviors when using dbt in Dagster:
        * During development, reload the manifest at run time to pick up any changes.
        * When deploying, expect a manifest that was created at build time to reduce start-up time.
        * Optionally handle a scenario when the dbt project is copied in to a directory for packaging.

        Args:
            project_dir (Union[str, Path]):
                The directory of the dbt project.
            target_folder (Union[str, Path]):
                The folder in the project directory to output artifacts.
                Default: "target"
            generate_artifacts_args (Sequence[List]):
                The dbt cli args to run to generate artifacts.
                Default: ["parse", "--quiet"]
            packaged_project_dir (Optional[Union[str, Path]]):
                A directory that will contain a copy of the dbt project and the manifest.json
                when the artifacts have been built. The prepare method will handle syncing
                the project_dir to this directory.
                This is useful when the dbt project needs to be part of the python package data
                like when deploying using PEX.
        """
        self.project_dir = Path(project_dir)
        if not self.project_dir.exists():
            raise DagsterDbtProjectNotFoundError(f"project_dir {project_dir} does not exist.")
        self.target_folder = Path(target_folder)
        # this is ok if it doesn't exist, will get created during sync
        self.packaged_project_dir = Path(packaged_project_dir) if packaged_project_dir else None
        self.generate_artifacts_args = generate_artifacts_args
        self.state_artifacts_path = (
            self._current_project_dir.joinpath(state_artifacts_folder)
            if state_artifacts_folder
            else None
        )

        if self.in_dev_env():
            self._manifest_path = self.generate_artifacts(
                log_level=logging.DEBUG,  # quiet logging for init time generation
            )
        else:
            self._manifest_path = self._current_project_dir.joinpath(
                self.target_folder, "manifest.json"
            )

    @property
    def _current_project_dir(self) -> Path:
        if self.in_dev_env():
            return self.packaged_project_dir if self.packaged_project_dir else self.project_dir

        return self.project_dir

    def in_dev_env(self) -> bool:
        # use built artifacts unless
        return (
            # launched via `dagster dev` cli
            bool(os.getenv("DAGSTER_IS_DEV_CLI"))
            or
            # or if explicitly opted in to loading at runtime
            bool(os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"))
        )

    @public
    @property
    def manifest_path(self) -> Path:
        """The path to the manifest.json, compiling the manifest first if in development or
        ensuring it already exists if not.
        """
        if not self._manifest_path.exists():
            if self.in_dev_env():
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
    def generate_artifacts(self, log_level: int = logging.DEBUG) -> Path:
        """Generate manifest.json and other dbt artifacts by invoking `dbt parse --quiet`.

        To customize artifact generation, subclass and override this method.

        Args:
            log_level (int):
                Log level for messages.
                Default: logging.DEBUG
        """
        from .core.resources_v2 import DbtCliResource

        logger.log(
            log_level,
            f"Creating manifest.json for {self.project_dir} using {self.generate_artifacts_args}.",
        )
        manifest_path = (
            DbtCliResource(project_dir=os.fspath(self.project_dir))
            .cli(
                self.generate_artifacts_args,
                target_path=self.target_folder,
            )
            .wait()
            .target_path.joinpath("manifest.json")
        )
        logger.log(log_level, f"Created {manifest_path}.")
        return manifest_path


@experimental
class DagsterDbtProjectManager:
    @public
    @classmethod
    def prepare_for_deployment(cls, project: DbtProject):
        """A method that can be called as part of the deployment process which runs the
        following preparation steps if appropriate.

            * generate_artifacts
            * sync_to_package_data

        Args:
            log_level (int):
                Log level for messages.
                Default: logging.INFO
        """
        project.generate_artifacts(log_level=logging.INFO)
        if project.packaged_project_dir:
            cls.sync_to_package_data(project)
        if project.state_artifacts_path:
            cls.manage_state_artifacts(project)

    @public
    @staticmethod
    def sync_to_package_data(project: DbtProject, *, log_level: int = logging.INFO):
        """Sync `project_dir` directory to `packaged_project_dir`.

        Args:
        log_level (int):
            Log level for messages.
            Default: logging.INFO
        """
        if project.packaged_project_dir is None:
            raise Exception(
                "sync_to_package_data should only be called if `packaged_project_dir` is set."
            )

        logger.log(
            log_level, f"Syncing project to package data directory {project.packaged_project_dir}."
        )
        if project.packaged_project_dir.exists():
            logger.log(log_level, f"Removing existing contents at {project.packaged_project_dir}.")
            shutil.rmtree(project.packaged_project_dir)

        # Determine if the package data dir is within the project dir, and ignore
        # that path if so.
        rel_path = Path(os.path.relpath(project.packaged_project_dir, project.project_dir))
        rel_ignore = ""
        if len(rel_path.parts) > 0 and rel_path.parts[0] != "..":
            rel_ignore = rel_path.parts[0]

        logger.log(log_level, f"Copying {project.project_dir} to {project.packaged_project_dir}.")
        shutil.copytree(
            src=project.project_dir,
            dst=project.packaged_project_dir,
            ignore=shutil.ignore_patterns(
                "*.git*",
                "*partial_parse.msgpack",
                rel_ignore,
            ),
        )
        logger.log(log_level, "Sync complete.")

    @public
    @staticmethod
    def manage_state_artifacts(project): ...
