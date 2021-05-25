import json
import os
import subprocess
from dataclasses import dataclass
from pprint import pprint
from tempfile import NamedTemporaryFile
from typing import Any, List, Optional

import yaml
from kubernetes.client.api_client import ApiClient
from schema.charts.dagster.values import DagsterHelmValues


def git_repo_root():
    return subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode("utf-8").strip()


@dataclass
class HelmTemplate:
    output: Optional[str] = None
    model: Optional[Any] = None
    name: str = "RELEASE-NAME"
    api_client: ApiClient = ApiClient()

    def render(self, values: DagsterHelmValues) -> List[Any]:
        with NamedTemporaryFile() as tmp_file:
            values_json = json.loads(values.json(exclude_none=True, by_alias=True))
            pprint(values_json)
            content = yaml.dump(values_json)
            tmp_file.write(content.encode())
            tmp_file.flush()

            command = [
                "helm",
                "template",
                self.name,
                os.path.join(git_repo_root(), "helm", "dagster"),
                "--debug",
                *["--values", tmp_file.name],
            ]

            if self.output:
                command += ["--show-only", self.output]

            templates = subprocess.check_output(command)

            print("\n--- Helm Templates ---")  # pylint: disable=print-call
            print(templates.decode())  # pylint: disable=print-call

            k8s_objects = [k8s_object for k8s_object in yaml.full_load_all(templates) if k8s_object]
            if self.model:
                k8s_objects = [
                    self.api_client._ApiClient__deserialize_model(  # pylint: disable=W0212
                        k8s_object, self.model
                    )
                    for k8s_object in k8s_objects
                ]

            return k8s_objects
