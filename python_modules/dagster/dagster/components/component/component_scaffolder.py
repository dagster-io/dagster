from dagster.components.scaffold.scaffold import Scaffolder, ScaffoldRequest


class DefaultComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest) -> None:
        # This will be deleted once all components are converted to the new ComponentScaffolder API
        from dagster.components.component_scaffolding import scaffold_component

        scaffold_component(request, {})
