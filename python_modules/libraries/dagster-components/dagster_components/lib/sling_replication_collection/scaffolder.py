import os
from pathlib import Path
from typing import Any

import yaml

from dagster_components.core.component_scaffolder import (
    ComponentScaffolder,
    ComponentScaffoldRequest,
)
from dagster_components.scaffold import scaffold_component_yaml


class SlingReplicationComponentScaffolder(ComponentScaffolder):
    def scaffold(self, request: ComponentScaffoldRequest, params: Any) -> None:
        scaffold_component_yaml(request, {"replications": [{"path": "replication.yaml"}]})
        replication_path = Path(os.getcwd()) / "replication.yaml"
        with open(replication_path, "w") as f:
            yaml.dump({"source": {}, "target": {}, "streams": {}}, f)
