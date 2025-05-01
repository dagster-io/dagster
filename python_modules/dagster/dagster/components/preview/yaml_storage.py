from typing import TYPE_CHECKING, Optional

from dagster._core.storage.components_storage.types import ComponentChangeOperation
from dagster.components.core.context import YamlComponentStorage
from dagster.components.preview.types import ComponentChange

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster.components.core.context import ComponentLoadContext


class PreviewYamlComponentStorage(YamlComponentStorage):
    def __init__(self, preview_changes: list[ComponentChange], instance: "DagsterInstance"):
        self._preview_changes = preview_changes
        self._instance = instance
        # replay the set of changes

    def _last_change_for_component_key(self, component_key: str) -> Optional[ComponentChange]:
        for change in reversed(self._preview_changes):
            # CHANGE TO USE ComponentKey object throughout
            if "/".join(change.component_key.path) == component_key:
                return change
        return None

    def is_in_storage(self, context: "ComponentLoadContext") -> bool:
        # if the component key has been deleted, this should return False? Or do
        # we need some clearer way of indicating that the component doesn't exist
        # any more so it doesn't fall back to some other loading path

        component_key = context.component_key

        last_preview_change = self._last_change_for_component_key(component_key)

        if not last_preview_change:
            return (context.path / "component.yaml").exists()

        if last_preview_change.operation == ComponentChangeOperation.DELETE:
            return False

        return True

    def read_declaration(self, context: "ComponentLoadContext") -> str:
        component_key = context.component_key

        last_preview_change = self._last_change_for_component_key(component_key)

        if last_preview_change:
            return self._instance.get_component_file_from_change(
                last_preview_change
            )  # load the file contenst from sha1

        return (context.path / "component.yaml").read_text()
