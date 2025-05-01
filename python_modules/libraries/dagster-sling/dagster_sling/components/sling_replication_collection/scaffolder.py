from typing import Any

import yaml
from dagster.components.component.component_scaffolder import Scaffolder, ScaffoldRequest
from dagster.components.component_scaffolding import scaffold_component


class SlingReplicationComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        replication_file_name = (
            "replication.yaml"
            if not request.is_subsequent_instance
            else f"replication_{request.yaml_instance_index}.yaml"
        )
        scaffold_component(request, {"replications": [{"path": replication_file_name}]})
        replication_path = request.target_path / replication_file_name
        with open(replication_path, "w") as f:
            yaml.dump({"source": {}, "target": {}, "streams": {}}, f)

    @classmethod
    def supports_multi_document_yaml(cls) -> bool:
        return True
