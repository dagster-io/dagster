from typing import Any

from dagster_components.scaffold.scaffold import Scaffolder, ScaffoldRequest


class DefaultComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        # This will be deleted once all components are converted to the new ComponentScaffolder API
        from dagster_components.component_scaffolding import scaffold_component_yaml

        scaffold_component_yaml(request, params.model_dump() if params else {})
