import pathlib

import yaml
from dagster_cloud_cli.config.models import ProcessedDagsterCloudConfig
from dagster_cloud_cli.entrypoint import app
from dagster_cloud_cli_tests.conftest import create_template_file
from typer.testing import CliRunner

DAGSTER_CLOUD_YAML_JINJA = """
defaults:
  container_context:
    k8s:
      env_vars:
        - environment={{ environment }}
      resources:
        requests:
          cpu: {{ resources.cpu }}
          memory: "{{ resources.memory }}"
        limits:
          cpu: {{ resources.cpu }}
          memory: "{{ resources.memory }}"
locations:
  - location_name: foo
    code_source:
      package_name: foo.definitions
    container_context:
      k8s:
        env_vars:
          - animal={{ animal_type }}
          {% for var in env_vars %}
          - {{ var.name }}={{ var.value }}
          {% endfor %}
"""

VALUES_JSON = """\
{
  "environment": "development",
  "resources": {
    "cpu": 1,
    "memory": "4Gi"
  }
}\
"""


def test_ci_template(temp_dir):
    with (
        create_template_file(
            temp_dir, "dagster_cloud.yaml.jinja", DAGSTER_CLOUD_YAML_JINJA
        ) as config_file,
        create_template_file(temp_dir, "values.json", VALUES_JSON) as values_file,
    ):
        runner = CliRunner()

        json_doc = '[{"name": "breed", "value": "golden retriever"}]'
        result = runner.invoke(
            app,
            [
                "ci",
                "template",
                "--project-dir",
                temp_dir,
                "--dagster-cloud-yaml-path",
                pathlib.Path(config_file).name,
                "--values-file",
                values_file,
                "--value",
                "animal_type=dog",
                "--value",
                f"env_vars={json_doc}",
            ],
        )
        assert result.exit_code == 0
        processed_config = ProcessedDagsterCloudConfig.model_validate(yaml.safe_load(result.stdout))
        assert len(processed_config.locations) == 1
        assert processed_config.locations[0].container_context is not None
        assert set(processed_config.locations[0].container_context["k8s"]["env_vars"]) == {
            "environment=development",
            "animal=dog",
            "breed=golden retriever",
        }
        assert processed_config.locations[0].container_context["k8s"]["resources"]["requests"] == {
            "cpu": 1,
            "memory": "4Gi",
        }
        assert processed_config.locations[0].container_context["k8s"]["resources"]["limits"] == {
            "cpu": 1,
            "memory": "4Gi",
        }
