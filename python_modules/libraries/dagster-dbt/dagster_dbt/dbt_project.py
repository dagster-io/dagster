import logging
import os
from pathlib import Path
from typing import Optional, Sequence, Union

from dagster._annotations import experimental
from dagster._model import DagsterModel

from .errors import DagsterDbtManifestNotFoundError, DagsterDbtProjectNotFoundError

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
            # If the project is intended to be packaged, create a symlink at the
            # packaged project directory to the project directory.
            if project.packaged_project_dir:
                if not project.packaged_project_dir.exists():
                    logger.info(
                        f"Creating symlink at packaged_project_dir `{project.packaged_project_dir}`"
                        f" to project_dir `{project.project_dir}`."
                    )

                    project.packaged_project_dir.symlink_to(project.project_dir)

                if not project.packaged_project_dir.is_symlink():
                    raise Exception(
                        f"The packaged_project_dir `{project.packaged_project_dir}` points to an"
                        " existing file or directory that is not a symlink to the"
                        f" project_dir `{project.project_dir}`, Remove it to continue."
                    )

                if project.packaged_project_dir.readlink() != project.project_dir:
                    raise Exception(
                        f"A symlink already exists at "
                        f" packaged_project_dir `{project.packaged_project_dir}`, but does not"
                        f" point to the project_dir `{project.project_dir}`. Remove it to continue."
                    )

            self.prepare(project)
            if not project.manifest_path.exists():
                raise DagsterDbtManifestNotFoundError(
                    f"Did not find manifest.json at expected path {project.manifest_path} "
                    f"after running '{self.prepare.__qualname__}'. Ensure the implementation respects "
                    "all DbtProject properties."
                )

    def prepare(self, project: "DbtProject") -> None:
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
class DbtProject(DagsterModel):
    project_dir: Path
    target_path: Path
    target: Optional[str]
    manifest_path: Path
    packaged_project_dir: Optional[Path]
    state_path: Optional[Path]
    manifest_preparer: DbtManifestPreparer

    def __init__(
        self,
        project_dir: Union[Path, str],
        *,
        target_path: Union[Path, str] = Path("target"),
        target: Optional[str] = None,
        packaged_project_dir: Optional[Union[Path, str]] = None,
        state_path: Optional[Union[Path, str]] = None,
        manifest_preparer: DbtManifestPreparer = DagsterDbtManifestPreparer(),
    ):
        """Representation of a dbt project.

        Args:
            project_path (Union[str, Path]):
                The directory of the dbt project.
            target_path (Union[str, Path]):
                The path, relative to the project directory, to output artifacts.
                Default: "target"
            target (Optional[str]):
                The target from your dbt `profiles.yml` to use for execution, if it should be explicitly set.
            state_path (Optional[Union[str, Path]]):
                The path, relative to the project directory, to reference artifacts from another run.
            manifest_preparer (Optional[DbtManifestPreparer]):
                A object for ensuring that manifest.json is in the right state at
                the right times.
                Default: DagsterDbtManifestPreparer
            packaged_project_dir (Optional[Union[str, Path]]):
                A directory that will contain a copy of the dbt project and the manifest.json
                when the artifacts have been built. The prepare method will handle syncing
                the project_path to this directory.
                This is useful when the dbt project needs to be part of the python package data
                like when deploying using PEX.
        """
        project_dir = Path(project_dir)
        if not project_dir.exists():
            raise DagsterDbtProjectNotFoundError(f"project_dir {project_dir} does not exist.")

        packaged_project_dir = Path(packaged_project_dir) if packaged_project_dir else None
        if (
            not manifest_preparer.using_dagster_dev()
            and packaged_project_dir
            and packaged_project_dir.exists()
        ):
            project_dir = packaged_project_dir

        manifest_path = project_dir.joinpath(target_path, "manifest.json")

        super().__init__(
            project_dir=project_dir,
            target_path=target_path,
            target=target,
            manifest_path=manifest_path,
            state_path=project_dir.joinpath(state_path) if state_path else None,
            packaged_project_dir=packaged_project_dir,
            manifest_preparer=manifest_preparer,
        )
        if manifest_preparer:
            manifest_preparer.on_load(self)
