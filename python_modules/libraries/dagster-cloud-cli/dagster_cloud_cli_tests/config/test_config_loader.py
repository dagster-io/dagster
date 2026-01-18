# pyright: reportOptionalMemberAccess=false, reportOptionalSubscript=false

from dagster_cloud_cli.config.loader import DagsterCloudLocationsConfigLoader
from dagster_cloud_cli.config.models import ProcessedDagsterCloudConfig
from dagster_cloud_cli_tests.conftest import create_template_file

DAGSTER_CLOUD_YAML_JINJA_TEMPLATE = """
{%- if defaults %}
defaults:
  {%- if defaults.build %}
  build:
    {{ defaults.build | to_yaml | indent(4, blank=True) }}
  {%- endif %}
  container_context:
    k8s:
      {%- if defaults.env_vars %}
      env_vars:
        {%- for env_var in defaults.env_vars %}
        - {{ env_var.name }}={{ env_var.value }}
        {%- endfor %}
      {%- endif %}
      {%- if defaults.config_maps %}
      env_config_map:
        {%- for config_map in defaults.config_maps %}
        - {{ config_map }}
        {%- endfor %}
      {%- endif %}
      resources:
        requests:
          cpu: "{{ defaults.cpu_request }}"
          memory: "{{ defaults.memory_request }}"
        limits:
          cpu: "{{ defaults.cpu_limit }}"
          memory: "{{ defaults.memory_limit}}"
{%- endif %}
locations:
{%- for location in locations %}
  - location_name: {{ location.name }}
    code_source:
      package_name: {{ location.package_name }}
    {%- if location.build %}
    build:
      {{ location.build | to_yaml | indent(6) }}
    {%- endif %}
    image: "{{ location.name }}"
    {%- if location.container_context.k8s %}
    container_context:
      k8s:
        {%- if location.container_context.k8s.env_vars %}
        env_vars:
          {% for env_var in location.container_context.k8s.env_vars %}
          - {{ env_var.name }}={{ env_var.value }}
          {%- endfor %}
        {%- endif %}
        {%- if location.container_context.k8s.resources %}
        resources:
          {{ location.container_context.k8s.resources | to_yaml | indent(10) }}
        {%- endif %}
    {%- endif %}
{%- endfor %}      
"""


def test_config_loader(tmpdir):
    context = {
        "defaults": {
            "build": {
                "registry": "my-registry.io/my-org",
            },
            "config_maps": ["global_config_map"],
            "cpu_request": "1",
            "memory_request": "1Gi",
            "cpu_limit": "2",
            "memory_limit": "2Gi",
            "env_vars": [{"name": "global", "value": "global"}],
        },
        "locations": [
            {
                "name": "foo",
                "package_name": "foo",
                "build": {"directory": "foo"},
                "container_context": {
                    "k8s": {
                        "env_vars": [
                            {"name": "foo", "value": "foo"},
                            {"name": "global", "value": "overridden"},
                        ],
                        "config_maps": ["my_config_map"],
                        "resources": {
                            "requests": {"memory": "32Gi"},
                            "limits": {"memory": "32Gi"},
                        },
                    }
                },
            }
        ],
    }

    with create_template_file(
        tmpdir, "template.jinja", DAGSTER_CLOUD_YAML_JINJA_TEMPLATE
    ) as template_file:
        loader = DagsterCloudLocationsConfigLoader()

        result = loader.load_from_template(template_file, context)
        assert isinstance(result, ProcessedDagsterCloudConfig)
        assert len(result.locations) == 1
        assert result.locations[0].location_name == "foo"
        assert result.locations[0].code_source.package_name == "foo"
        assert result.locations[0].build.model_dump() == {
            "directory": "foo",
            "registry": "my-registry.io/my-org",
        }
        assert result.locations[0].image == "foo"
        assert set(result.locations[0].container_context["k8s"]["env_vars"]) == {
            "foo=foo",
            "global=overridden",
        }
        assert result.locations[0].container_context["k8s"]["resources"] == {
            "requests": {"cpu": "1", "memory": "32Gi"},
            "limits": {"cpu": "2", "memory": "32Gi"},
        }
