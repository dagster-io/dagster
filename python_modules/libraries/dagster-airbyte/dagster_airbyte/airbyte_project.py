import logging
import os
from pathlib import Path
from typing import Optional, Union

from dagster import ResourceDefinition
from dagster._annotations import public
from dagster._record import IHaveNew, record_custom

from dagster_airbyte.resources import AirbyteResource

logger = logging.getLogger("dagster-airbyte.project")


# TODO: duplicate from dbt_project.py, projects could inherit from one common project?
def using_dagster_dev() -> bool:
    return bool(os.getenv("DAGSTER_IS_DEV_CLI"))


class AirbyteProjectPreparer:
    """The abstract class of a preparer for an AirbyteProject representation."""

    @public
    def prepare_if_dev(self, project: "AirbyteProject") -> None:
        """Invoked in the `prepare_if_dev` method of AirbyteProject,
        when Airbyte needs preparation during development.
        """

    @public
    def prepare(self, project: "AirbyteProject") -> None:
        """Called explicitly to prepare the connection metadata for this the project."""

    @public
    def using_dagster_dev(self) -> bool:
        """Returns true if Dagster is running using the `dagster dev` command."""
        return using_dagster_dev()


class AirbyteInstanceProjectPreparer(AirbyteProjectPreparer):
    def __init__(
        self,
        instance: Union[AirbyteResource, ResourceDefinition],
    ):
        pass


class AirbyteOctaviaProjectPreparer(AirbyteProjectPreparer):
    def __init__(
        self,
        project_dir: Path,
    ):
        pass


@record_custom
class AirbyteProject(IHaveNew):
    preparer: AirbyteProjectPreparer
    workspace_id: Optional[str]

    def __new__(
        cls,
        preparer: AirbyteProjectPreparer,
        workspace_id: Optional[str] = None,
    ) -> "AirbyteProject":
        return super().__new__(
            cls,
            workspace_id=workspace_id,
            preparer=preparer,
        )

    @public
    def prepare_if_dev(self) -> None:
        if self.preparer:
            self.preparer.prepare_if_dev(self)

    @staticmethod
    def from_instance(
        instance: Union[AirbyteResource, ResourceDefinition],
        workspace_id: Optional[str] = None,
    ) -> "AirbyteProject":
        return AirbyteProject(
            preparer=AirbyteInstanceProjectPreparer(instance=instance), workspace_id=workspace_id
        )

    @staticmethod
    def from_octavia_project(
        project_dir: Union[Path, str],
        workspace_id: Optional[str] = None,
    ) -> "AirbyteProject":
        project_dir = Path(project_dir)
        if not project_dir.exists():
            # TODO: implement custom errors
            raise FileNotFoundError(f"project_dir {project_dir} does not exist.")

        return AirbyteProject(
            preparer=AirbyteOctaviaProjectPreparer(project_dir=project_dir),
            workspace_id=workspace_id,
        )
