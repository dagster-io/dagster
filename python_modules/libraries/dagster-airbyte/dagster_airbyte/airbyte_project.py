import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, cast

import yaml
from dagster import (
    ResourceDefinition,
    _check as check,
)
from dagster._annotations import public
from dagster._record import IHaveNew, record_custom
from dagster._utils import run_with_concurrent_update_guard

from dagster_airbyte.asset_defs import AirbyteConnectionMetadata
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
    def prepare_if_dev(self, project: "AirbyteProject"):
        raise NotImplementedError()

    def prepare(self, project: "AirbyteProject") -> None:
        raise NotImplementedError()


class AirbyteLocalProjectPreparer(AirbyteProjectPreparer):
    def prepare_if_dev(self, project: "AirbyteProject"):
        if self.using_dagster_dev():
            self.prepare(project)
            if not project.connections_metadata_path.exists():
                # TODO: implement custom errors
                raise FileNotFoundError(
                    f"Did not find connections metadata at expected path {project.connections_metadata_path} "
                    f"after running '{self.prepare.__qualname__}'. Ensure the implementation respects "
                    "all Airbyte configuration properties."
                )

    def prepare(self, project: "AirbyteProject") -> None:
        # guard against multiple Dagster processes trying to update this at the same time
        run_with_concurrent_update_guard(
            project.connections_metadata_path,
            self._prepare_connections_metadata,
            project=project,
        )

    def _prepare_connections_metadata(self, project: "AirbyteProject") -> None:
        connections_dir = Path(os.path.join(project.configuration_dir, "connections"))
        if not connections_dir.exists():
            # TODO: implement custom errors
            raise FileNotFoundError(
                f"Did not find connections directory at expected path {connections_dir} "
                f"after running '{self.prepare.__qualname__}'. Ensure the implementation respects "
                "all Airbyte configuration properties."
            )

        output_connections: List[Dict[str, AirbyteConnectionMetadata]] = []

        connection_directories = os.listdir(connections_dir)
        for connection_name in connection_directories:
            connection_dir = os.path.join(connections_dir, connection_name)
            with open(os.path.join(connection_dir, "configuration.yaml"), encoding="utf-8") as f:
                connection = AirbyteConnectionMetadata.from_config(yaml.safe_load(f.read()))

            if project.workspace_id:
                state_file = f"state_{project.workspace_id}.yaml"
                check.invariant(
                    state_file in os.listdir(connection_dir),
                    f"Workspace state file {state_file} not found",
                )
            else:
                state_files = [
                    filename
                    for filename in os.listdir(connection_dir)
                    if filename.startswith("state_")
                ]
                check.invariant(
                    len(state_files) > 0,
                    f"No state files found for connection {connection_name} in {connection_dir}",
                )
                check.invariant(
                    len(state_files) <= 1,
                    f"More than one state file found for connection {connection_name} in {connection_dir}, "
                    "specify a workspace_id to disambiguate",
                )
                state_file = state_files[0]

            with open(os.path.join(connection_dir, cast(str, state_file)), encoding="utf-8") as f:
                state = yaml.safe_load(f.read())
                connection_id = state.get("resource_id")

            output_connections.append({connection_id: connection})

        with open(project.connections_metadata_path, encoding="utf-8") as f:
            json.dump(output_connections, f)


@record_custom
class AirbyteProject(IHaveNew):
    configuration_dir: Path
    preparer: AirbyteProjectPreparer
    workspace_id: Optional[str]
    output_path: Path
    connections_metadata_path: Path

    def __new__(
        cls,
        configuration_dir: Path,
        preparer: AirbyteProjectPreparer,
        workspace_id: Optional[str] = None,
    ) -> "AirbyteProject":
        return super().__new__(
            cls,
            configuration_dir=configuration_dir,
            workspace_id=workspace_id,
            preparer=preparer,
        )

    @property
    def connections_metadata(self) -> List[Dict[str, AirbyteConnectionMetadata]]:
        if not self.connections_metadata_path.exists():
            # TODO: implement custom errors
            raise FileNotFoundError(
                f"Did not find connections metadata at expected path {self.connections_metadata_path}. "
                f"Ensure the Airbyte project was prepared."
            )
        with open(self.connections_metadata_path, encoding="utf-8") as f:
            connections_metadata_json = json.load(f)

        return [
            {connection_id: AirbyteConnectionMetadata(**connection_metadata)}
            for connection_id, connection_metadata in connections_metadata_json
        ]

    @public
    def prepare_if_dev(self) -> None:
        if self.preparer:
            self.preparer.prepare_if_dev(self)

    @staticmethod
    def from_instance(
        instance: Union[AirbyteResource, ResourceDefinition],
        workspace_id: Optional[str] = None,
    ) -> "AirbyteProject":
        raise NotImplementedError()
        # return AirbyteProject(
        #     preparer=AirbyteInstanceProjectPreparer(instance=instance), workspace_id=workspace_id
        # )

    @staticmethod
    def from_local_configuration(
        configuration_dir: Union[Path, str],
        workspace_id: Optional[str] = None,
    ) -> "AirbyteProject":
        configuration_dir = Path(configuration_dir)
        if not configuration_dir.exists():
            # TODO: implement custom errors
            raise FileNotFoundError(f"configuration_dir {configuration_dir} does not exist.")

        return AirbyteProject(
            configuration_dir=configuration_dir,
            preparer=AirbyteLocalProjectPreparer(),
            workspace_id=workspace_id,
        )
