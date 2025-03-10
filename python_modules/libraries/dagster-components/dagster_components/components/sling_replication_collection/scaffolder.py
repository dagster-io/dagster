from typing import Any

import yaml

from dagster_components.component_scaffolding import scaffold_component_yaml
from dagster_components.core.component_blueprint import Blueprint, ScaffoldRequest


class SlingReplicationComponentBlueprint(Blueprint):
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        scaffold_component_yaml(request, {"replications": [{"path": "replication.yaml"}]})
        replication_path = request.target_path / "replication.yaml"
        with open(replication_path, "w") as f:
            yaml.dump({"source": {}, "target": {}, "streams": {}}, f)
