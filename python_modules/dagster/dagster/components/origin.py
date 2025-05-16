from pathlib import Path

from dagster_shared.record import record

from dagster.components.component.component import Component


@record
class ComponentOrigin:
    project_root: Path
    root_component: Component
    project_root: Path
