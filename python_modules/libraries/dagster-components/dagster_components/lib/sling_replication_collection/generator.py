import os
from pathlib import Path
from typing import Any

import yaml

from dagster_components.core.component_generator import ComponentGenerateRequest, ComponentGenerator
from dagster_components.generate import generate_component_yaml


class SlingReplicationComponentGenerator(ComponentGenerator):
    def generate_files(self, request: ComponentGenerateRequest, params: Any) -> None:
        generate_component_yaml(request, {"replications": [{"path": "replication.yaml"}]})
        replication_path = Path(os.getcwd()) / "replication.yaml"
        with open(replication_path, "w") as f:
            yaml.dump({"source": {}, "target": {}, "streams": {}}, f)
