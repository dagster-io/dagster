from pathlib import Path

from dagster_components import ComponentLoadContext
from dagster_components.core.component_declaration import component_declaration
from dagster_components.lib.definitions_component import DefinitionsComponent


@component_declaration
def load_component(context: ComponentLoadContext) -> DefinitionsComponent:
    return DefinitionsComponent(definitions_path=Path(__file__).parent / "definitions.py")
