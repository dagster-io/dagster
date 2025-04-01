from typing import Any

import yaml
from dagster.components.component.component_scaffolder import Scaffolder, ScaffoldRequest
from dagster.components.component_scaffolding import scaffold_component


class SlingReplicationComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        scaffold_component(request, {"replications": [{"path": "replication.yaml"}]})
        replication_path = request.target_path / "replication.yaml"
        with open(replication_path, "w") as f:
            yaml.dump({"source": {}, "target": {}, "streams": {}}, f)
