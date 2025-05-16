from dagster_shared.record import record

from dagster.components.component.component import Component


@record
class ComponentOrigin:
    root_component: Component
