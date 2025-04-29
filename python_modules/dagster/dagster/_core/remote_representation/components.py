import hashlib
import json
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, cast

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._config.pythonic_config.type_check_utils import safe_is_subclass
from dagster.components.component.component import Component
from dagster.components.core.defs_module import DagsterDefsComponent, DefsFolderComponent

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import ComponentsDetails


@whitelist_for_serdes
@record
class ComponentInstanceFileSnap:
    file_path: Sequence[str]
    sha1: str


@whitelist_for_serdes
@record
class ComponentInstanceSnap:
    key: str
    type: str
    files: Sequence[ComponentInstanceFileSnap]


@whitelist_for_serdes
@record
class ComponentTypeSnap:
    name: str
    schema: Optional[str]
    description: Optional[str]
    # path: Path  # defs relative


@whitelist_for_serdes
@record
class ComponentManifest:
    types: Sequence[ComponentTypeSnap]
    instances: Sequence[ComponentInstanceSnap]
    git_root_to_defs_root: Sequence[str]

    @staticmethod
    def from_details(details: "ComponentsDetails"):
        if details is None:
            return None

        types = []
        componeny_key_by_cls = {}
        for key, plugin in details.plugins.items():
            if safe_is_subclass(plugin, Component):
                plugin_component = cast("type[Component]", plugin)
                schema = plugin_component.get_schema()
                description = plugin_component.get_description()
                schema = schema.model_json_schema() if schema else None
                componeny_key_by_cls[plugin_component] = key.to_typename()
                types.append(
                    ComponentTypeSnap(
                        name=key.to_typename(),
                        schema=json.dumps(schema) if schema else None,
                        description=description,
                    )
                )

        instances = []
        root_component: DefsFolderComponent = details.root_component
        for key, component in list(root_component.iterate_components()):
            if isinstance(component, (DefsFolderComponent, DagsterDefsComponent)):
                continue
            instances.append(
                ComponentInstanceSnap(
                    key=str(key.relative_to(root_component.path)),
                    type=componeny_key_by_cls[component.__class__],
                    files=[
                        ComponentInstanceFileSnap(
                            file_path=file,
                            sha1=hashlib.sha1(
                                (key.joinpath(*file)).read_text().encode("utf-8")
                            ).hexdigest(),
                        )
                        for file in [["component.yaml"]]
                    ],
                )
            )

        return ComponentManifest(
            types=types,
            instances=instances,
            git_root_to_defs_root=details.git_root_to_defs_root,
        )
