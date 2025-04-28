from collections.abc import Sequence

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes


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

    @staticmethod
    def from_details(details):
        if details is None:
            return None

        types = []
        for key, plugin in details.plugins.items():
            types.append(
                ComponentTypeSnap(
                    name=plugin.__name__,
                )
            )

        instances = []
        for key, component in list(details.root_component.iterate_components()):
            instances.append(
                ComponentInstanceSnap(
                    key=str(key.relative_to(details.root_component.path)),
                    type=component.__class__.__name__,
                )
            )

        return ComponentManifest(
            types=types,
            instances=instances,
        )
