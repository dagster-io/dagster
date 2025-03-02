from typing import Any

import yaml

from dagster_components.core.component_scaffolder import Scaffolder, ScaffoldRequest
from dagster_components.scaffold import scaffold_component_yaml


class SlingReplicationComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        scaffold_component_yaml(request, {"replications": [{"path": "replication.yaml"}]})
        replication_path = request.component_instance_root_path / "replication.yaml"
        with open(replication_path, "w") as f:
            yaml.dump({"source": {}, "target": {}, "streams": {}}, f)
