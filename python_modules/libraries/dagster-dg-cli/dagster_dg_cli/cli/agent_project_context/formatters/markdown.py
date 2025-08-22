"""Markdown formatter for project context."""

from dagster_dg_cli.cli.agent_project_context.formatters import BaseFormatter
from dagster_dg_cli.cli.agent_project_context.models import ProjectContext
from dagster_dg_cli.cli.agent_project_context.schema_utils import generate_yaml_template_from_schema


class MarkdownFormatter(BaseFormatter):
    """Formats project context as Markdown."""

    def format(self, context: ProjectContext) -> str:
        """Format project context as Markdown."""
        lines = []
        lines.append("## Available Project Context\n")

        # Project Info
        if context.project_name != "Unknown":
            lines.append(f"**Project:** {context.project_name}")
        lines.append(f"**Root:** {context.project_root}")
        lines.append("")

        # Available Components
        if context.components:
            lines.append(f"**Available Components:** {len(context.components)} detected\n")
            for comp in context.components:
                lines.append(f"• **{comp.key}**: {comp.summary}")
            lines.append("")
        else:
            lines.append("**Available Components:** None detected\n")

        # Project Structure Overview
        lines.append("**Project Structure:**")
        if context.project_structure.has_pyproject_toml:
            lines.append("• Has pyproject.toml")
        if context.project_structure.has_dbt_project:
            dbt_paths = context.project_structure.dbt_project_paths
            lines.append(f"• Has dbt project(s): {len(dbt_paths)} found")

        packages = context.project_structure.python_packages
        if packages:
            dagster_packages = [p for p in packages if p["name"].startswith("dagster")]
            lines.append(
                f"• Python packages: {len(packages)} total, {len(dagster_packages)} Dagster-related"
            )
        lines.append("")

        # dbt Components (if any)
        if context.dbt_schemas:
            lines.append("### dbt Component Details\n")
            for component_key, schema_info in context.dbt_schemas.items():
                lines.append(f"#### {component_key}\n")

                desc = schema_info.description
                if desc:
                    lines.append(f"**Description:** {desc}\n")

                # Show schema template
                comp_schema = schema_info.component_schema
                if comp_schema:
                    lines.append("**Configuration Template:**")
                    template = generate_yaml_template_from_schema(
                        comp_schema, component_key.split(".")[-1]
                    )
                    # Indent each line
                    for line in template.split("\n"):
                        lines.append(f"  {line}" if line.strip() else "")
                    lines.append("")

        # Integrations
        if context.integrations:
            lines.append(f"**Available Integrations ({len(context.integrations)} total):**\n")
            for integ in context.integrations:
                lines.append(f"• **{integ.name}**: {integ.description}")
                lines.append(f"  - Package: {integ.pypi}")
            lines.append("")
        else:
            lines.append("**Available Integrations:** None detected")

        return "\n".join(lines)
