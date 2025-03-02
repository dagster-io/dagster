from dataclasses import dataclass
from typing import Any

from dagster_components.scaffoldable.scaffolder import ComponentScaffolder, ComponentScaffoldRequest


@dataclass
class ComponentScaffolderUnavailableReason:
    message: str


class DefaultComponentScaffolder(ComponentScaffolder):
    def scaffold(self, request: ComponentScaffoldRequest, params: Any) -> None:
        # This will be deleted once all components are converted to the new ComponentScaffolder API
        from dagster_components.scaffold import scaffold_component_yaml

        scaffold_component_yaml(request, params.model_dump() if params else {})
