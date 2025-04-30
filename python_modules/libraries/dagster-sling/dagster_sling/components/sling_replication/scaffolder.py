from typing import Any

import yaml
from dagster.components import Scaffolder, ScaffoldRequest, scaffold_component


class SlingReplicationComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        scaffold_component(request, {"replication": {"path": "replication.yaml"}})
        replication_path = request.target_path / "replication.yaml"
        with open(replication_path, "w") as f:
            yaml.dump({"source": {}, "target": {}, "streams": {}}, f)
