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
        for plugin in details.plugins:
            types.append(
                ComponentTypeSnap(
                    name=plugin.__class__.__name__,
                )
            )

        instances = []
        for key, component in details.root_component.get_all_components().items():
            instances.append(
                ComponentInstanceSnap(
                    key=key,
                    type=component.__class__.__name__,
                )
            )

        return ComponentManifest(
            types=types,
            instances=instances,
        )
