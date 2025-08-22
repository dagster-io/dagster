"""Output formatters for project context."""

from abc import ABC, abstractmethod

from dagster_dg_cli.cli.agent_project_context.models import ProjectContext


class BaseFormatter(ABC):
    """Base class for project context formatters."""

    @abstractmethod
    def format(self, context: ProjectContext) -> str:
        """Format project context into string output."""
        pass


def get_formatter(format_name: str) -> BaseFormatter:
    """Get formatter instance by name."""
    from dagster_dg_cli.cli.agent_project_context.formatters.json import JsonFormatter
    from dagster_dg_cli.cli.agent_project_context.formatters.markdown import MarkdownFormatter
    from dagster_dg_cli.cli.agent_project_context.formatters.xml import XmlFormatter

    formatters = {
        "json": JsonFormatter,
        "markdown": MarkdownFormatter,
        "xml": XmlFormatter,
    }

    formatter_class = formatters.get(format_name)
    if not formatter_class:
        raise ValueError(f"Unknown format: {format_name}")

    return formatter_class()
