"""dbt resources and assets."""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Union

import dagster as dg
from dagster_dbt import (
    DagsterDbtTranslator,
    DbtCliResource,
    DbtProject,
    dbt_assets,
    group_from_dbt_resource_props_fallback_to_directory,
)
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    """Custom translator that assigns asset groups based on dbt folder structure."""

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> str | None:
        """Assign group name based on dbt model folder structure."""
        return group_from_dbt_resource_props_fallback_to_directory(dbt_resource_props)


class DbtCliResourceHelper:
    """Helper class for DbtCliResource operations."""

    @staticmethod
    def find_project_dir() -> str:
        """Find dbt_project directory."""
        env_dir = os.getenv("DBT_PROJECT_DIR")
        if env_dir and os.path.exists(env_dir):
            return os.path.abspath(env_dir)

        current_file_dir = os.path.dirname(os.path.abspath(__file__))

        dagster_snowflake_dir = os.path.abspath(
            os.path.join(current_file_dir, "..", "..", "..", "..")
        )
        repo_root = os.path.abspath(os.path.join(dagster_snowflake_dir, ".."))

        possible_paths = [
            os.path.join(repo_root, "dbt_project"),
            os.path.join(dagster_snowflake_dir, "dbt_project"),
            os.path.join(os.path.abspath(os.path.join(repo_root, "..")), "dbt_project"),
        ]

        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path) and os.path.isdir(abs_path):
                return abs_path

        raise FileNotFoundError(
            f"Could not find dbt_project directory. Tried: {', '.join(possible_paths)}. "
            "Set DBT_PROJECT_DIR environment variable to specify the path."
        )


def get_dbt_resource() -> DbtCliResource:
    """Get configured DbtCliResource instance."""
    dbt_project_dir = DbtCliResourceHelper.find_project_dir()
    dbt_profiles_dir = os.getenv("DBT_PROFILES_DIR", dbt_project_dir)

    return DbtCliResource(
        project_dir=dbt_project_dir,
        profiles_dir=dbt_profiles_dir,
    )


dbt_project_dir = DbtCliResourceHelper.find_project_dir()
dbt_project = DbtProject(project_dir=dbt_project_dir)


dbt_project.prepare_if_dev()


manifest_path = dbt_project.manifest_path

if not os.path.exists(manifest_path):
    import warnings

    warnings.warn(
        f"dbt manifest not found at {manifest_path}. "
        "Run 'dagster dev' to auto-generate or 'dbt parse' to create manually.",
        UserWarning,
        stacklevel=2,
    )
    dbt_transform_assets: list[Any] = []  # type: ignore[assignment]
else:

    @dbt_assets(
        manifest=manifest_path,
        select="stg_stories stg_sentiment int_story_enrichment int_entity_aggregates fct_daily_stories dim_story_categories story_trends",
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def dbt_transform_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()
