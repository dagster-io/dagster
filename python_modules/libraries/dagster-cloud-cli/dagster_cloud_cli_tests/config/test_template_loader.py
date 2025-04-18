import yaml
from dagster_cloud_cli.config.jinja_template_loader import JinjaTemplateLoader
from dagster_cloud_cli_tests.conftest import create_template_file


def test_template_loader(tmpdir, monkeypatch):
    context = {"name": "dagster", "default_environment": "test"}

    template = "Hello {{ name }}, you are in {{ get_env('ENVIRONMENT', default_environment) }}."

    with create_template_file(tmpdir, "template.jinja", template) as template_file:
        result = JinjaTemplateLoader().render(template_file, context)
        assert result == "Hello dagster, you are in test."

        monkeypatch.setenv("ENVIRONMENT", "development")
        result = JinjaTemplateLoader().render(template_file, context)
        assert result == "Hello dagster, you are in development."


ARTICLES_TEMPLATE = """
articles:
{%- for article in articles %}
- {{ article | to_yaml(indent=2, default_flow_style=False) | indent(2) }}
{%- endfor %}
"""


def test_template_loader_to_yaml_filter(tmpdir):
    context = {
        "articles": [
            {
                "attributes": {
                    "author": "Dagster's engineering team",
                },
                "name": "dagster",
                "summary": "Dagster is an awesome data orchestrator.",
                "tags": ["data", "orchestration"],
            }
        ]
    }

    with create_template_file(tmpdir, "template.jinja", ARTICLES_TEMPLATE) as template_file:
        result = JinjaTemplateLoader().render(template_file, context)
        roundtrip = yaml.safe_load(result)
        assert roundtrip == context
