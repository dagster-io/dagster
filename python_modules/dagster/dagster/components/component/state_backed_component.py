import tempfile
from abc import abstractmethod
from pathlib import Path
from typing import Optional
from uuid import uuid4

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_load_context import DefinitionsLoadContext
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext


class StateBackedComponent(Component):
    def get_state_key(self, context: ComponentLoadContext) -> str:
        return context.path.relative_to(context.defs_module_path).as_posix().replace("/", "_")

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        key = self.get_state_key(context)

        with DefinitionsLoadContext.get().temp_state_path(key) as state_path:
            return self.build_defs_from_state(context, state_path=state_path)

    def refresh_state(self, context: ComponentLoadContext) -> None:
        """Rebuilds the state for this component and persists it to the current StateStore."""
        key = self.get_state_key(context)
        state_storage = DefsStateStorage.get_current()
        if state_storage is None:
            raise DagsterInvalidInvocationError(
                f"Attempted to refresh state of {key} without a StateStorage in context. "
                "This is likely the result of an internal framework error."
            )
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / key
            self.write_state_to_path(state_path)
            state_storage.upload_state_from_path(key, version=str(uuid4()), path=state_path)

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
    def write_state_to_path(self, state_path: Path):
        """Fetches and writes required state to a local file."""
        raise NotImplementedError()
