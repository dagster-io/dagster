from pathlib import Path

from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.context import DgContext
from dagster_dg.docs import markdown_for_component_type

dg_context = DgContext.default()
registry = RemoteComponentRegistry.from_dg_context(dg_context)

for key in registry.global_keys():
    markdown = markdown_for_component_type(registry.get_global(key))

    component_md_path = (
        Path(__file__).parent.parent / "docs" / "api" / "components" / f"{key.to_typename()}.md"
    )
    component_md_path.parent.mkdir(parents=True, exist_ok=True)
    component_md_path.write_text(markdown)
