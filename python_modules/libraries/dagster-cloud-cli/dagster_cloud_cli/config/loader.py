from typing import Any

from dagster_cloud_cli.config.jinja_template_loader import JinjaTemplateLoader
from dagster_cloud_cli.config.merger import DagsterCloudConfigDefaultsMerger
from dagster_cloud_cli.config.models import ProcessedDagsterCloudConfig, load_dagster_cloud_yaml


class DagsterCloudLocationsConfigLoader:
    """Load a Dagster Cloud config from a template, with context values, merge in defaults to code location
    and return a ProcessedDagsterCloudConfig object.
    """

    @staticmethod
    def load_from_template(
        template_file: str, context: dict[str, Any]
    ) -> ProcessedDagsterCloudConfig:
        template_loader = JinjaTemplateLoader()
        template = template_loader.render(template_file, context)

        dagster_cloud_config = load_dagster_cloud_yaml(template)

        config_merger = DagsterCloudConfigDefaultsMerger()
        return config_merger.process(dagster_cloud_config)
