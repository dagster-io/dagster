"""XML formatter for project context."""

from dagster_dg_cli.cli.agent_project_context.formatters import BaseFormatter
from dagster_dg_cli.cli.agent_project_context.models import ProjectContext
from dagster_dg_cli.cli.agent_project_context.schema_utils import generate_yaml_template_from_schema


def _xml_escape(text: str) -> str:
    """Escape special XML characters."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


class XmlFormatter(BaseFormatter):
    """Formats project context as XML."""

    def format(self, context: ProjectContext) -> str:
        """Format project context as XML.

        Uses XML tags for multi-section prompts as recommended by Anthropic:
        https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags
        """
        lines = []
        lines.append("<project_context>")

        # Project info section
        lines.append("  <project_info>")
        lines.append(f"    <name>{_xml_escape(context.project_name)}</name>")
        lines.append(f"    <root>{_xml_escape(context.project_root)}</root>")
        lines.append(
            f"    <working_directory>{_xml_escape(context.working_directory)}</working_directory>"
        )
        lines.append("  </project_info>")

        # Components section
        lines.append(f'  <components count="{len(context.components)}">')
        for comp in context.components:
            lines.append(
                f'    <component key="{_xml_escape(comp.key)}" namespace="{_xml_escape(comp.namespace)}" name="{_xml_escape(comp.name)}">'
            )
            lines.append(f"      <summary>{_xml_escape(comp.summary)}</summary>")
            lines.append("    </component>")
        lines.append("  </components>")

        # Project structure section
        lines.append("  <project_structure>")
        lines.append(
            f"    <has_pyproject_toml>{str(context.project_structure.has_pyproject_toml).lower()}</has_pyproject_toml>"
        )
        lines.append(
            f'    <dbt_projects count="{len(context.project_structure.dbt_project_paths)}">'
        )
        for path in context.project_structure.dbt_project_paths:
            lines.append(f"      <path>{_xml_escape(path)}</path>")
        lines.append("    </dbt_projects>")

        packages = context.project_structure.python_packages
        dagster_packages = [p for p in packages if p["name"].startswith("dagster")]
        lines.append(
            f'    <python_packages total="{len(packages)}" dagster_related="{len(dagster_packages)}"/>'
        )
        lines.append("  </project_structure>")

        # dbt schemas section
        if context.dbt_schemas:
            lines.append("  <dbt_schemas>")
            for component_key, schema_info in context.dbt_schemas.items():
                lines.append(f'    <component key="{_xml_escape(component_key)}">')
                lines.append(
                    f"      <description>{_xml_escape(schema_info.description)}</description>"
                )

                # Generate YAML template for configuration
                if schema_info.component_schema:
                    template = generate_yaml_template_from_schema(
                        schema_info.component_schema, component_key.split(".")[-1]
                    )
                    lines.append("      <configuration_template>")
                    lines.append("<![CDATA[")
                    lines.append(template)
                    lines.append("]]>")
                    lines.append("      </configuration_template>")

                lines.append("    </component>")
            lines.append("  </dbt_schemas>")

        # Integrations section
        lines.append(f'  <integrations count="{len(context.integrations)}">')
        for integ in context.integrations:
            lines.append("    <integration>")
            lines.append(f"      <name>{_xml_escape(integ.name)}</name>")
            lines.append(f"      <description>{_xml_escape(integ.description)}</description>")
            lines.append(f"      <pypi>{_xml_escape(integ.pypi)}</pypi>")
            lines.append("    </integration>")
        lines.append("  </integrations>")

        lines.append("</project_context>")
        return "\n".join(lines)
