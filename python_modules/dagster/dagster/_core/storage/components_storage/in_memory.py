import json
from collections import defaultdict
from itertools import chain
from typing import Optional

from dagster._core.definitions.selector import RepositorySelector
from dagster._core.storage.components_storage.types import ComponentChange, ComponentKey


class InMemoryComponentStorage:
    def __init__(self):
        self._component_changes: dict[str, dict[str, list[ComponentChange]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def insert_component_change(self, component_change: ComponentChange) -> None:
        self._component_changes[component_change.repository_selector.selector_id][
            json.dumps(component_change.component_key.path)
        ].append(component_change)

    def get_component_changes(
        self, repository_selector: RepositorySelector, component_key: Optional[ComponentKey] = None
    ) -> list[ComponentChange]:
        changes_for_repo = self._component_changes[repository_selector.selector_id]
        if component_key:
            return changes_for_repo[json.dumps(component_key.path)]
        return list(chain.from_iterable(changes_for_repo.values()))
