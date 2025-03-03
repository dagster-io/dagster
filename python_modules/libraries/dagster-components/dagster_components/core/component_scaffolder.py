from typing import Any

from dagster_components.scaffoldable.scaffolder import Scaffolder, ScaffoldRequest


class DefaultComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        # This will be deleted once all components are converted to the new ComponentScaffolder API
        from dagster_components.scaffold import scaffold_component_yaml

        scaffold_component_yaml(request, params.model_dump() if params else {})
