"""Data collection functions for project context."""

import json
import subprocess
from pathlib import Path
from typing import Any, Union

from dagster_dg_core.component import EnvRegistry
from dagster_dg_core.context import DgContext

from dagster_dg_cli.cli.agent_project_context.models import (
    ComponentInfo,
    ComponentSchema,
    IntegrationInfo,
    ProjectContext,
    ProjectStructure,
)


def _safe_get_project_name(dg_context: DgContext) -> Union[str, None]:
    """Safely get project name, returning None if not in a project context."""
    try:
        return dg_context.project_name
    except Exception:
        return None


def _collect_project_context(dg_context: DgContext, registry: EnvRegistry) -> ProjectContext:
    """Collect all project context information into a structured format."""
    # Gather components info
    components = []
    for comp_info in _get_components_info(registry):
        components.append(
            ComponentInfo(
                key=comp_info["key"],
                summary=comp_info["summary"],
                namespace=comp_info["namespace"],
                name=comp_info["name"],
            )
        )

    # Gather integrations info
    integrations = []
    for integ_info in _get_integrations_info():
        integrations.append(
            IntegrationInfo(
                name=integ_info["name"],
                description=integ_info["description"],
                pypi=integ_info["pypi"],
            )
        )

    # Gather project structure info
    structure_info = _get_project_structure(dg_context)
    project_structure = ProjectStructure(
        has_pyproject_toml=structure_info["has_pyproject_toml"],
        has_dbt_project=structure_info["has_dbt_project"],
        dbt_project_paths=structure_info["dbt_project_paths"],
        python_packages=structure_info["python_packages"],
    )

    # Gather dbt schemas
    dbt_schemas = {}
    for key, schema_info in _get_dbt_component_schemas(registry).items():
        dbt_schemas[key] = ComponentSchema(
            description=schema_info["description"],
            scaffold_params_schema=schema_info["scaffold_params_schema"],
            component_schema=schema_info["component_schema"],
        )

    return ProjectContext(
        project_name=_safe_get_project_name(dg_context) or "Unknown",
        project_root=str(dg_context.root_path),
        working_directory=str(Path.cwd()),
        components=components,
        integrations=integrations,
        project_structure=project_structure,
        dbt_schemas=dbt_schemas,
    )


def _get_components_info(registry: EnvRegistry) -> list[dict[str, Any]]:
    """Get information about available components."""
    component_objects = sorted(
        registry.get_objects(feature="component"), key=lambda x: x.key.to_typename()
    )

    return [
        {
            "key": obj.key.to_typename(),
            "summary": obj.summary,
            "namespace": obj.key.namespace,
            "name": obj.key.name,
        }
        for obj in component_objects
    ]


def _get_integrations_info() -> list[dict[str, Any]]:
    """Get information about available integrations using dg docs integrations command."""
    try:
        # Run the dg docs integrations --json command
        result = subprocess.run(
            ["dg", "docs", "integrations", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode == 0:
            payload = json.loads(result.stdout)

            # Filter to only include complete entries
            filtered_integrations = []
            for integration in payload:
                if (
                    integration.get("name")
                    and integration.get("description")
                    and integration.get("pypi")
                ):
                    filtered_integrations.append(
                        {
                            "name": integration["name"],
                            "description": integration["description"],
                            "pypi": integration["pypi"],
                        }
                    )

            return filtered_integrations
    except Exception:
        # If we can't get integrations, return empty list rather than failing
        pass

    return []


def _get_installed_python_packages() -> list[dict[str, Any]]:
    """Get list of installed Python packages using uv pip list."""
    try:
        # Try uv pip list first
        result = subprocess.run(
            ["uv", "pip", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        if result.returncode == 0:
            packages = json.loads(result.stdout)
            return [
                {
                    "name": pkg["name"],
                    "version": pkg["version"],
                    "editable": pkg.get("editable_project_location") is not None,
                }
                for pkg in packages
            ]

        # Fallback to regular pip list if uv is not available
        result = subprocess.run(
            ["pip", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        if result.returncode == 0:
            packages = json.loads(result.stdout)
            return [
                {
                    "name": pkg["name"],
                    "version": pkg["version"],
                    "editable": pkg.get("editable_project_location") is not None,
                }
                for pkg in packages
            ]

    except Exception:
        # If package listing fails, return empty list
        pass

    return []


def _get_project_structure(dg_context: DgContext) -> dict[str, Any]:
    """Get basic project structure information."""
    structure = {
        "has_pyproject_toml": (dg_context.root_path / "pyproject.toml").exists(),
        "has_dbt_project": False,
        "dbt_project_paths": [],
        "python_packages": _get_installed_python_packages(),
    }

    # Look for dbt projects
    for path in dg_context.root_path.rglob("dbt_project.yml"):
        structure["has_dbt_project"] = True
        structure["dbt_project_paths"].append(str(path.relative_to(dg_context.root_path)))

    return structure


def _get_dbt_component_schemas(registry: EnvRegistry) -> dict[str, Any]:
    """Get schema information for dbt-related components."""
    schemas = {}

    # Look for dbt components
    for obj in registry.get_objects(feature="component"):
        if "dbt" in obj.key.to_typename().lower():
            try:
                entry_snap = registry.get(obj.key)
                schemas[obj.key.to_typename()] = {
                    "description": entry_snap.description,
                    "scaffold_params_schema": entry_snap.scaffolder_schema,
                    "component_schema": entry_snap.component_schema,
                }
            except Exception:
                # If we can't get schema info, skip it
                continue

    return schemas
