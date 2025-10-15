import asyncio
import inspect
import shutil
import tempfile
from abc import abstractmethod
from collections.abc import Awaitable
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union
from uuid import uuid4

from dagster_shared import check
from dagster_shared.serdes.objects.models.defs_state_info import (
    CODE_SERVER_STATE_VERSION,
    LOCAL_STATE_VERSION,
    DefsStateManagementType,
)
from typing_extensions import Self

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._utils.env import using_dagster_dev
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.utils.defs_state import DefsStateConfig
from dagster.components.utils.project_paths import get_local_state_path

if TYPE_CHECKING:
    from pydantic import BaseModel


class StateBackedComponent(Component):
    @classmethod
    def load(cls, attributes: Optional["BaseModel"], context: "ComponentLoadContext") -> Self:
        """Loads the component and marks its defs_state_key on the component tree."""
        loaded_component = super().load(attributes, context)
        context.component_tree.mark_component_defs_state_key(
            defs_state_key=loaded_component.defs_state_config.key,
            component_path=context.component_path,
        )
        return loaded_component

    @property
    @abstractmethod
    def defs_state_config(self) -> DefsStateConfig: ...

    async def _write_state_to_path_async(self, state_path: Path) -> None:
        if inspect.iscoroutinefunction(self.write_state_to_path):
            await self.write_state_to_path(state_path)
        else:
            await asyncio.to_thread(self.write_state_to_path, state_path)

    async def _store_code_server_state(self, key: str, state_storage: DefsStateStorage) -> str:
        load_context = DefinitionsLoadContext.get()
        check.invariant(
            load_context.load_type == DefinitionsLoadType.INITIALIZATION,
            "Attempted to store LEGACY_CODE_SERVER_SNAPSHOTS state outside of the initialization phase.",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state"
            await self._write_state_to_path_async(state_path)
            load_context.add_code_server_defs_state_info(key, state_path.read_text())
            state_storage.set_latest_version(key, CODE_SERVER_STATE_VERSION)
            return CODE_SERVER_STATE_VERSION

    async def _store_local_filesystem_state(
        self, key: str, state_storage: DefsStateStorage, project_root: Path
    ) -> str:
        state_path = get_local_state_path(key, project_root)
        shutil.rmtree(state_path, ignore_errors=True)
        await self._write_state_to_path_async(state_path)
        state_storage.set_latest_version(key, LOCAL_STATE_VERSION)
        return LOCAL_STATE_VERSION

    async def _store_versioned_state_storage_state(
        self, key: str, state_storage: DefsStateStorage
    ) -> str:
        with tempfile.TemporaryDirectory() as temp_dir:
            version = str(uuid4())
            state_path = Path(temp_dir) / "state"
            await self._write_state_to_path_async(state_path)
            state_storage.upload_state_from_path(key, version=version, path=state_path)
            return version

    async def refresh_state(self, project_root: Path) -> str:
        """Rebuilds the state for this component and persists it to the current StateStore.

        Args:
            project_root: The root directory of the project.
        """
        key = self.defs_state_config.key
        state_storage = DefsStateStorage.get()
        if state_storage is None:
            raise DagsterInvalidInvocationError(
                f"Attempted to refresh state of {key} without a StateStorage in context. "
                "This is likely the result of an internal framework error."
            )

        if self.defs_state_config.type == DefsStateManagementType.VERSIONED_STATE_STORAGE:
            return await self._store_versioned_state_storage_state(key, state_storage)
        elif self.defs_state_config.type == DefsStateManagementType.LOCAL_FILESYSTEM:
            return await self._store_local_filesystem_state(key, state_storage, project_root)
        elif self.defs_state_config.type == DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS:
            check.invariant(
                DefinitionsLoadContext.get().load_type == DefinitionsLoadType.INITIALIZATION,
                "Attempted to refresh `LEGACY_CODE_SERVER_SNAPSHOTS` state explicitly, but this can only happen during code server startup.",
            )
            return await self._store_code_server_state(key, state_storage)
        else:
            raise DagsterInvalidInvocationError(
                f"Invalid state storage location: {self.defs_state_config.type}"
            )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        key = self.defs_state_config.key
        defs_load_context = DefinitionsLoadContext.get()
        state_storage = DefsStateStorage.get()
        if state_storage is None:
            raise DagsterInvalidInvocationError(
                "Attempted to build defs without a StateStorage in context. "
                "This is likely the result of an internal framework error."
            )

        if defs_load_context.load_type == DefinitionsLoadType.INITIALIZATION:
            if (
                # for code server state management, we always refresh the state
                (
                    self.defs_state_config.type
                    == DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS
                )
                or
                # automatically refresh in local dev unless the user opts out
                (using_dagster_dev() and self.defs_state_config.refresh_if_dev)
            ):
                version = asyncio.run(self.refresh_state(context.project_root))
                defs_load_context.add_defs_state_info(key, version)

        with DefinitionsLoadContext.get().state_path(
            self.defs_state_config, state_storage, context.project_root
        ) as state_path:
            return self.build_defs_from_state(context, state_path=state_path)

    @abstractmethod
    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> Definitions:
        """Given a state_path, builds a Definitions object based on the state
        contained at that path.

        Args:
            context (ComponentLoadContext): The context associated with this component load.
            state_path (Optional[Path]): The path to the state file. If no state has been
                previously written to the state store, this will be set to None.

        Returns:
            Definitions: The Definitions object built from the state.
        """

    @abstractmethod
    def write_state_to_path(self, state_path: Path) -> Union[None, Awaitable[None]]:
        """Fetches and writes required state to a local file. This method can be
        implemented as either sync or async.

        Args:
            state_path (Path): The path to the state file.
        """
        raise NotImplementedError()
