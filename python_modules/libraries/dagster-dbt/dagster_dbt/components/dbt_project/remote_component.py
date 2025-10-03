import asyncio
import shutil
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.model import Model
from dagster_shared.serdes.objects.models.defs_state_info import (
    DefsStateStorageLocation,
    get_local_state_dir,
)
from git import Repo

from dagster_dbt.components.dbt_project.component import DbtProjectComponent
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dbt_project import DbtProject


class RemoteGitDbtProject(Resolvable, Model):
    url: str
    token: Optional[str]
    clone_path: str = "./cloned_dbt"
    repo_relative_path: str = "."

    def _local_path(self, key: str, location: DefsStateStorageLocation) -> Path:
        if location == DefsStateStorageLocation.LOCAL:
            return get_local_state_dir(key) / "project"
        return Path(self.clone_path) / self.repo_relative_path

    def get_local_project(self, key: str, location: DefsStateStorageLocation) -> DbtProject:
        return DbtProject(project_dir=self._local_path(key, location))

    async def fetch(self, key: str, location: DefsStateStorageLocation) -> None:
        await asyncio.sleep(6)
        with tempfile.TemporaryDirectory() as temp_dir:
            Repo.clone_from(self.url, temp_dir)
            shutil.copytree(
                Path(temp_dir) / self.repo_relative_path,
                self._local_path(key, location),
                dirs_exist_ok=True,
            )


@dataclass
class RemoteDbtProjectComponent(StateBackedComponent, DbtProjectComponent):
    project: RemoteGitDbtProject  # type: ignore
    storage_location: Literal["LOCAL", "REMOTE"] = "REMOTE"

    @property
    def local_project(self) -> DbtProject:
        key = self.get_defs_state_key()
        return self.project.get_local_project(key, self._state_storage_location)

    @property
    def _state_storage_location(self) -> DefsStateStorageLocation:
        return DefsStateStorageLocation(self.storage_location)

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        if self._state_storage_location == DefsStateStorageLocation.REMOTE:
            context.log.info("Fetching remote project")
            asyncio.run(self.project.fetch(self.get_defs_state_key(), self._state_storage_location))
            context.log.info("Successfully fetched remote project")
        yield from super().execute(context, dbt)

    async def write_state_to_path(self, state_path: Path) -> None:
        # download the project locally
        await self.project.fetch(self.get_defs_state_key(), self._state_storage_location)
        # compile the manifest
        self.local_project.preparer.prepare(self.local_project)
        # copy the manifest file to the state path
        shutil.copy(self.local_project.manifest_path, state_path)

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> Definitions:
        if state_path is None:
            return Definitions()

        if self._state_storage_location == DefsStateStorageLocation.REMOTE:
            # move the manifest file to the expected spot
            shutil.copy(state_path, self.local_project.manifest_path)

        return DbtProjectComponent.build_defs(self, context)
