import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pprint import pprint
from tempfile import NamedTemporaryFile, mkstemp
from typing import Any, List, Optional, Union

import yaml
from kubernetes.client.api_client import ApiClient
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.values import DagsterUserDeploymentsHelmValues


def git_repo_root():
    return subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode("utf-8").strip()


@dataclass
class HelmTemplate:
    helm_dir_path: str
    subchart_paths: List[str]
    output: Optional[str] = None
    model: Optional[Any] = None
    name: str = "release-name"
    api_client: ApiClient = ApiClient()

    def render(
        self,
        values: Union[DagsterHelmValues, DagsterUserDeploymentsHelmValues],
        chart_version: Optional[str] = None,
    ) -> List[Any]:
        with NamedTemporaryFile() as tmp_file:
            helm_dir_path = os.path.join(git_repo_root(), self.helm_dir_path)

            values_json = json.loads(values.json(exclude_none=True, by_alias=True))
            pprint(values_json)
            content = yaml.dump(values_json)
            tmp_file.write(content.encode())
            tmp_file.flush()

            command = [
                "helm",
                "template",
                self.name,
                helm_dir_path,
                "--debug",
                *["--values", tmp_file.name],
            ]

            if self.output:
                ## Uncomment to render all templates before filtering to surface Helm templating
                ## errors with better error messages
                # subprocess.check_output(command)

                command += ["--show-only", self.output]

            with self._with_chart_yaml(helm_dir_path, chart_version):
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

    @contextmanager
    def _with_chart_yaml(self, helm_dir_path: str, chart_version: Optional[str]):
        if not chart_version:
            yield
        else:
            umbrella_chart_path = os.path.join(helm_dir_path, "Chart.yaml")
            subchart_chart_paths = [
                os.path.join(helm_dir_path, subchart_path, "Chart.yaml")
                for subchart_path in self.subchart_paths
            ]

            chart_paths = subchart_chart_paths + [umbrella_chart_path]
            chart_copy_paths = []
            for chart_path in chart_paths:
                _, chart_copy_path = mkstemp()
                shutil.copy2(chart_path, chart_copy_path)
                chart_copy_paths.append(chart_copy_path)

                with open(chart_path, encoding="utf8") as chart_file:
                    old_chart_yaml = yaml.safe_load(chart_file)

                with open(chart_path, "w", encoding="utf8") as chart_file:
                    new_chart_yaml = old_chart_yaml.copy()
                    new_chart_yaml["version"] = chart_version
                    yaml.dump(new_chart_yaml, chart_file)

            yield

            for chart_path, chart_copy_path in zip(chart_paths, chart_copy_paths):
                shutil.copy2(chart_copy_path, chart_path)
                os.remove(chart_copy_path)
