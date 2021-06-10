import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pprint import pprint
from tempfile import NamedTemporaryFile, mkstemp
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

    def render(self, values: DagsterHelmValues, chart_version: Optional[str] = None) -> List[Any]:
        with NamedTemporaryFile() as tmp_file:
            helm_dir_path = os.path.join(git_repo_root(), "helm", "dagster")

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
                # render all templates before filtering to surface Helm templating errors
                # with better error messages
                subprocess.check_output(command)

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
            subchart_chart_path = os.path.join(
                helm_dir_path, "charts/dagster-user-deployments/Chart.yaml"
            )

            _, umbrella_chart_copy_path = mkstemp()
            _, subchart_copy_path = mkstemp()

            shutil.copy2(umbrella_chart_path, umbrella_chart_copy_path)
            shutil.copy2(subchart_chart_path, subchart_copy_path)

            with open(umbrella_chart_path) as umbrella_chart_file, open(
                subchart_chart_path
            ) as subchart_chart_file:
                old_umbrella_chart_yaml = yaml.safe_load(umbrella_chart_file)
                old_subchart_chart_yaml = yaml.safe_load(subchart_chart_file)

            with open(umbrella_chart_path, "w") as umbrella_chart_file, open(
                subchart_chart_path, "w"
            ) as subchart_file:
                new_umbrella_chart_yaml = old_umbrella_chart_yaml.copy()
                new_subchart_chart_yaml = old_subchart_chart_yaml.copy()

                new_umbrella_chart_yaml["version"] = chart_version
                new_subchart_chart_yaml["version"] = chart_version

                yaml.dump(new_umbrella_chart_yaml, umbrella_chart_file)
                yaml.dump(new_subchart_chart_yaml, subchart_file)

            yield

            shutil.copy2(umbrella_chart_copy_path, umbrella_chart_path)
            shutil.copy2(subchart_copy_path, subchart_chart_path)
            os.remove(umbrella_chart_copy_path)
            os.remove(subchart_copy_path)
