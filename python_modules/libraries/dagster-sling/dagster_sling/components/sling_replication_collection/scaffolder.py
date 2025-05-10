import yaml
from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest


class SlingReplicationComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest) -> None:
        scaffold_component(request, {"replications": [{"path": "replication.yaml"}]})
        replication_path = request.target_path / "replication.yaml"
        with open(replication_path, "w") as f:
            yaml.dump({"source": {}, "target": {}, "streams": {}}, f)
