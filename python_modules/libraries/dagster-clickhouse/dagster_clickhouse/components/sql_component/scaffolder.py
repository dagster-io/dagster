from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest


class ClickhouseQueryComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest) -> None:
        scaffold_component(
            request,
            {
                "host": "localhost",
                "port": 9000,
                "user": "default",
                "password": "",
            },
        )
