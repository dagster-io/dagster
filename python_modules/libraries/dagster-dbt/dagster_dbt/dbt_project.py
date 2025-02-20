import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Optional, Union

import yaml
from dagster._annotations import public
from dagster._record import IHaveNew, record_custom
from dagster._utils import run_with_concurrent_update_guard

from dagster_dbt.errors import (
    DagsterDbtManifestNotFoundError,
    DagsterDbtProfilesDirectoryNotFoundError,
    DagsterDbtProjectNotFoundError,
    DagsterDbtProjectYmlFileNotFoundError,
)

logger = logging.getLogger("dagster-dbt.artifacts")


def using_dagster_dev() -> bool:
    return bool(os.getenv("DAGSTER_IS_DEV_CLI"))


class DbtProjectPreparer:
    """The abstract class of a preparer for a DbtProject representation.

    When implemented, this handler should provide an experience of:
        * The behavior expected during development and at run time, in the `on_load` method.
        * The implementation of the preparation process, in the `prepare` method.
    """

    @public
    def prepare_if_dev(self, project: "DbtProject") -> None:
        """Invoked in the `prepare_if_dev` method of DbtProject,
        when DbtProject needs preparation during development.
        """

    @public
    def prepare(self, project: "DbtProject") -> None:
        """Called explicitly to prepare the manifest for this the project."""

    @public
    def using_dagster_dev(self) -> bool:
        """Returns true if Dagster is running using the `dagster dev` command."""
        return using_dagster_dev()


class DagsterDbtProjectPreparer(DbtProjectPreparer):
    def __init__(
        self,
        generate_cli_args: Optional[Sequence[str]] = None,
    ):
        """The default DbtProjectPreparer, this handler provides an experience of:
            * During development, reload the manifest at run time to pick up any changes.
            * When deploying, expect a manifest that was created at build time to reduce start-up time.

        Args:
            generate_cli_args (Sequence[str]):
                The arguments to pass to the dbt cli to generate a manifest.json.
                Default: ["parse", "--quiet"]
        """
        self._generate_cli_args = generate_cli_args or ["parse", "--quiet"]

    @public
    def prepare_if_dev(self, project: "DbtProject"):
        """Handle the preparation process during development and at run time.

        The preparation process is executed if the condition is met,
        i.e. if the self.using_dagster_dev is true.

        This method returns successfully if a loadable manifest file at the expected path.

        Args:
            project (DbtProject):
                The dbt project to be prepared.
        """
        if self.using_dagster_dev():
            self.prepare(project)
            if not project.manifest_path.exists():
                raise DagsterDbtManifestNotFoundError(
                    f"Did not find manifest.json at expected path {project.manifest_path} "
                    f"after running '{self.prepare.__qualname__}'. Ensure the implementation respects "
                    "all DbtProject properties."
                )

    @public
    def prepare(self, project: "DbtProject") -> None:
        """Execute the preparation process.

        The preparation process:
            * pulls and installs the dependencies of the dbt project,
            * parses the dbt project and created a loadable manifest file.

        Args:
            project (DbtProject):
                The dbt project to be prepared.
        """
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
        from dagster_dbt.core.resource import DbtCliResource

        (
            DbtCliResource(project_dir=project)
            .cli(["deps", "--quiet"], target_path=project.target_path)
            .wait()
        )

    def _prepare_manifest(self, project: "DbtProject") -> None:
        from dagster_dbt.core.resource import DbtCliResource

        (
            DbtCliResource(project_dir=project)
            .cli(
                self._generate_cli_args,
                target_path=project.target_path,
            )
            .wait()
        )


@record_custom
class DbtProject(IHaveNew):
    """Representation of a dbt project and related settings that assist with managing the project preparation.

    Using this helps achieve a setup where the dbt manifest file
    and dbt dependencies are available and up-to-date:
    * during development, pull the dependencies and reload the manifest at run time to pick up any changes.
    * when deployed, expect a manifest that was created at build time to reduce start-up time.

    The cli ``dagster-dbt project prepare-and-package`` can be used as part of the deployment process to
    handle the project preparation.

    This object can be passed directly to :py:class:`~dagster_dbt.DbtCliResource`.

    Args:
        project_dir (Union[str, Path]):
            The directory of the dbt project.
        target_path (Union[str, Path]):
            The path, relative to the project directory, to output artifacts.
            It corresponds to the target path in dbt.
            Default: "target"
        profiles_dir (Union[str, Path]):
            The path to the directory containing your dbt `profiles.yml`.
            By default, the current working directory is used, which is the dbt project directory.
        profile (Optional[str]):
            The profile from your dbt `profiles.yml` to use for execution, if it should be explicitly set.
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

    name: str
    project_dir: Path
    target_path: Path
    profiles_dir: Path
    profile: Optional[str]
    target: Optional[str]
    manifest_path: Path
    packaged_project_dir: Optional[Path]
    state_path: Optional[Path]
    has_uninstalled_deps: bool
    preparer: DbtProjectPreparer

    def __new__(
        cls,
        project_dir: Union[Path, str],
        *,
        target_path: Union[Path, str] = Path("target"),
        profiles_dir: Optional[Union[Path, str]] = None,
        profile: Optional[str] = None,
        target: Optional[str] = None,
        packaged_project_dir: Optional[Union[Path, str]] = None,
        state_path: Optional[Union[Path, str]] = None,
    ) -> "DbtProject":
        project_dir = Path(project_dir)
        if not project_dir.exists():
            raise DagsterDbtProjectNotFoundError(f"project_dir {project_dir} does not exist.")

        packaged_project_dir = Path(packaged_project_dir) if packaged_project_dir else None
        if not using_dagster_dev() and packaged_project_dir and packaged_project_dir.exists():
            project_dir = packaged_project_dir

        # Handling the profiles_dir must be done after the packaged_project_dir is handled
        profiles_dir = Path(profiles_dir) if profiles_dir else project_dir
        if not profiles_dir.exists():
            raise DagsterDbtProfilesDirectoryNotFoundError(
                f"profiles {profiles_dir} does not exist."
            )

        preparer = DagsterDbtProjectPreparer()

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

        return super().__new__(
            cls,
            name=dbt_project_yml["name"],
            project_dir=project_dir,
            target_path=target_path,
            profiles_dir=profiles_dir,
            profile=profile,
            target=target,
            manifest_path=manifest_path,
            state_path=project_dir.joinpath(state_path) if state_path else None,
            packaged_project_dir=packaged_project_dir,
            has_uninstalled_deps=has_uninstalled_deps,
            preparer=preparer,
        )

    @public
    def prepare_if_dev(self) -> None:
        """Prepare a dbt project at run time during development, i.e. when `dagster dev` is used.
        This method has no effect outside this development context.

        The preparation process ensures that the dbt manifest file and dbt dependencies are available and up-to-date.
        During development, it pulls the dependencies and reloads the manifest at run time to pick up any changes.

        If this method returns successfully, `self.manifest_path` will point to a loadable manifest file.
        This method causes errors if the manifest file has not been correctly created by the preparation process.

        Examples:
            Preparing a DbtProject during development:

            .. code-block:: python

                from pathlib import Path

                from dagster import Definitions
                from dagster_dbt import DbtProject

                my_project = DbtProject(project_dir=Path("path/to/dbt_project"))
                my_project.prepare_if_dev()

                defs = Definitions(
                    resources={
                        "dbt": DbtCliResource(project_dir=my_project),
                    },
                    ...
                )
        """
        if self.preparer:
            self.preparer.prepare_if_dev(self)
