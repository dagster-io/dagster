import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Protocol, Sequence, Union, runtime_checkable

from dagster._annotations import experimental
from dagster._model import DagsterModel

from .errors import DagsterDbtProjectNotFoundError

logger = logging.getLogger("dagster-dbt.artifacts")


def using_dagster_dev() -> bool:
    return bool(os.getenv("DAGSTER_IS_DEV_CLI"))


def parse_on_load_opt_in() -> bool:
    return bool(os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"))


@runtime_checkable
class ManifestInitFn(Protocol):
    def __call__(self, project: "DbtProject", *, deploying: bool) -> None: ...


def dagster_dbt_manifest_init(
    project: "DbtProject",
    deploying: bool,
    generate_cli_args: Sequence = ("parse", "--quiet"),
):
    """A dbt manifest init function that helps achieve the behaviors:
    * During development, reload the manifest at run time to pick up any changes.
    * When deploying, expect a manifest that was created at build time to reduce start-up time.

    The default generate_cli_args of ("parse", "--quiet") can be overridden using functools.partial
    or writing another function that calls this one with that argument set.
    """
    from .core.resources_v2 import DbtCliResource

    if deploying or using_dagster_dev() or parse_on_load_opt_in():
        DbtCliResource(project_dir=os.fspath(project.project_dir)).cli(
            generate_cli_args,
            target_path=project.target_dir,
        ).wait()


@experimental
class DbtProject(DagsterModel):
    project_dir: Path
    target_dir: Path
    manifest_path: Path
    packaged_project_dir: Optional[Path]
    manifest_init_fn: Optional[ManifestInitFn]

    def __init__(
        self,
        project_dir: Union[Path, str],
        *,
        target_dir: Union[Path, str] = "target",
        packaged_project_dir: Optional[Union[Path, str]] = None,
        manifest_init_fn: Optional[ManifestInitFn] = dagster_dbt_manifest_init,
    ):
        """Representation of a dbt project.

        Args:
            project_path (Union[str, Path]):
                The directory of the dbt project.
            target_dir (Union[str, Path]):
                The folder in the project directory to output artifacts.
                Default: "target"
            manifest_init_fn (Optional[ManifestInitFn]):
                A function invoked at init time and via prepare_for_deployment
                that can be used to ensure the manifest.json is in the right state at
                the right times.
                Default: dagster_dbt_manifest_init
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
            packaged_project_dir=packaged_project_dir,
            manifest_init_fn=manifest_init_fn,
        )
        if manifest_init_fn:
            manifest_init_fn(self, deploying=False)


def prepare_for_deployment(project: DbtProject):
    """A method that can be called as part of the deployment process which runs the
    following preparation steps if appropriate:
        * project.manifest_init_fn(project, deploying=True)
        * sync_project_to_packaged_dir.
    """
    if project.manifest_init_fn:
        logger.info(f"Running manifest init function {project.manifest_init_fn.__qualname__}.")
        project.manifest_init_fn(project, deploying=True)
        logger.info("Manifest init complete.")

    if project.packaged_project_dir:
        sync_project_to_packaged_dir(project)


def sync_project_to_packaged_dir(
    project: DbtProject,
):
    """Sync a `DbtProject`s `project_dir` directory to its `packaged_project_dir`."""
    if project.packaged_project_dir is None:
        raise Exception(
            "sync_project_to_packaged_dir should only be called if `packaged_project_dir` is set."
        )

    logger.info(f"Syncing project to package data directory {project.packaged_project_dir}.")
    if project.packaged_project_dir.exists():
        logger.info(f"Removing existing contents at {project.packaged_project_dir}.")
        shutil.rmtree(project.packaged_project_dir)

    # Determine if the package data dir is within the project dir, and ignore
    # that path if so.
    rel_path = Path(os.path.relpath(project.packaged_project_dir, project.project_dir))
    rel_ignore = ""
    if len(rel_path.parts) > 0 and rel_path.parts[0] != "..":
        rel_ignore = rel_path.parts[0]

    logger.info(f"Copying {project.project_dir} to {project.packaged_project_dir}.")
    shutil.copytree(
        src=project.project_dir,
        dst=project.packaged_project_dir,
        ignore=shutil.ignore_patterns(
            "*.git*",
            "*partial_parse.msgpack",
            rel_ignore,
        ),
    )
    logger.info("Sync complete.")
