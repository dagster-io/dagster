import tempfile
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from typing_extensions import Self

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_load_context import DefinitionsLoadContext
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext

if TYPE_CHECKING:
    from pydantic import BaseModel


class StateBackedComponent(Component):
    @classmethod
    def load(cls, attributes: Optional["BaseModel"], context: "ComponentLoadContext") -> Self:
        """Loads the component and marks its defs_state_key on the component tree."""
        loaded_component = super().load(attributes, context)
        context.component_tree.mark_component_defs_state_key(
            defs_state_key=loaded_component.get_defs_state_key(),
            component_path=context.component_path,
        )
        return loaded_component

    def get_defs_state_key(self) -> str:
        """Returns a key that uniquely identifies the state for this component."""
        return self.__class__.__name__

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        key = self.get_defs_state_key()

        with DefinitionsLoadContext.get().temp_state_path(key) as state_path:
            return self.build_defs_from_state(context, state_path=state_path)

    async def refresh_state(self) -> None:
        """Rebuilds the state for this component and persists it to the current StateStore."""
        key = self.get_defs_state_key()
        state_storage = DefsStateStorage.get()
        if state_storage is None:
            raise DagsterInvalidInvocationError(
                f"Attempted to refresh state of {key} without a StateStorage in context. "
                "This is likely the result of an internal framework error."
            )
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / key
            await self.write_state_to_path(state_path)
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
    async def write_state_to_path(self, state_path: Path):
        """Fetches and writes required state to a local file."""
        raise NotImplementedError()
