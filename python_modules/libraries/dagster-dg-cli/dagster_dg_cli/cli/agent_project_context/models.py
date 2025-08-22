"""Data models for agent project context."""

from typing import Any

from dagster_shared.record import record


@record
class ComponentInfo:
    """Information about a single component."""

    key: str
    summary: str
    namespace: str
    name: str


@record
class IntegrationInfo:
    """Information about a single integration."""

    name: str
    description: str
    pypi: str


@record
class ProjectStructure:
    """Project structure information."""

    has_pyproject_toml: bool
    has_dbt_project: bool
    dbt_project_paths: list[str]
    python_packages: list[dict[str, Any]]


@record
class ComponentSchema:
    """Component schema information."""

    description: str
    scaffold_params_schema: dict[str, Any]
    component_schema: dict[str, Any]


@record
class ProjectContext:
    """Structured representation of project context for AI consumption."""

    # Basic project info
    project_name: str
    project_root: str
    working_directory: str

    # Components and integrations
    components: list[ComponentInfo]
    integrations: list[IntegrationInfo]

    # Project structure
    project_structure: ProjectStructure

    # dbt-specific schemas
    dbt_schemas: dict[str, ComponentSchema]
