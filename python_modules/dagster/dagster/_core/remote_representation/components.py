from collections.abc import Sequence
from typing import TYPE_CHECKING

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster.components.core.defs_module import DagsterDefsComponent, DefsFolderComponent

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import ComponentsDetails


@whitelist_for_serdes
@record
class ComponentInstanceSnap:
    key: str
    type: str
    # path: Path  # defs relative


@whitelist_for_serdes
@record
class ComponentTypeSnap:
    name: str
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
        for key, plugin in details.plugins.items():
            types.append(
                ComponentTypeSnap(
                    name=plugin.__name__,  # type: ignore
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
                    type=component.__class__.__name__,
                )
            )

        return ComponentManifest(
            types=types,
            instances=instances,
            git_root_to_defs_root=details.git_root_to_defs_root,
        )
