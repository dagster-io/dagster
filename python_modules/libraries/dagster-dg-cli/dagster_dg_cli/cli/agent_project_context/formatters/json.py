"""JSON formatter for project context."""

import json

from dagster_dg_cli.cli.agent_project_context.formatters import BaseFormatter
from dagster_dg_cli.cli.agent_project_context.models import ProjectContext


class JsonFormatter(BaseFormatter):
    """Formats project context as JSON."""

    def format(self, context: ProjectContext) -> str:
        """Format project context as JSON."""
        # Convert record objects to dictionaries for JSON serialization
        context_dict = {
            "working_directory": context.working_directory,
            "project_root": context.project_root,
            "project_name": context.project_name,
            "components": [
                {
                    "key": comp.key,
                    "summary": comp.summary,
                    "namespace": comp.namespace,
                    "name": comp.name,
                }
                for comp in context.components
            ],
            "integrations": [
                {
                    "name": integ.name,
                    "description": integ.description,
                    "pypi": integ.pypi,
                }
                for integ in context.integrations
            ],
            "project_structure": {
                "has_pyproject_toml": context.project_structure.has_pyproject_toml,
                "has_dbt_project": context.project_structure.has_dbt_project,
                "dbt_project_paths": context.project_structure.dbt_project_paths,
                "python_packages": context.project_structure.python_packages,
            },
            "dbt_schemas": {
                key: {
                    "description": schema.description,
                    "scaffold_params_schema": schema.scaffold_params_schema,
                    "component_schema": schema.component_schema,
                }
                for key, schema in context.dbt_schemas.items()
            },
        }
        return json.dumps(context_dict, indent=2)
