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
            DbtCliResource(project_dir=os.fspath(project.project_dir))
            .cli(
                self._generate_cli_args,
                target_path=project.target_dir,
            )
            .wait()
        )


@experimental
class DbtProject(DagsterModel):
    project_dir: Path
    target_dir: Path
    manifest_path: Path
    state_dir: Optional[Path]
    packaged_project_dir: Optional[Path]
    manifest_preparer: DbtManifestPreparer

    def __init__(
        self,
        project_dir: Union[Path, str],
        *,
        target_dir: Union[Path, str] = "target",
        state_dir: Optional[Union[Path, str]] = None,
        packaged_project_dir: Optional[Union[Path, str]] = None,
        manifest_preparer: DbtManifestPreparer = DagsterDbtManifestPreparer(),
    ):
        """Representation of a dbt project.

        Args:
            project_path (Union[str, Path]):
                The directory of the dbt project.
            target_dir (Union[str, Path]):
                The folder in the project directory to output artifacts.
                Default: "target"
            state_dir (Optional[Union[str, Path]]):
                The folder in the project directory to reference artifacts from another run.
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
        if using_dagster_dev() and packaged_project_dir:
            current_project_dir = packaged_project_dir
        else:
            current_project_dir = project_dir

        manifest_path = current_project_dir.joinpath(target_dir, "manifest.json")

        super().__init__(
            project_dir=project_dir,
            target_dir=target_dir,
            manifest_path=manifest_path,
            state_dir=current_project_dir.joinpath(state_dir) if state_dir else None,
            packaged_project_dir=packaged_project_dir,
            manifest_preparer=manifest_preparer,
        )
        if manifest_preparer:
            manifest_preparer.on_load(self)
