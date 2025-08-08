from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import yaml
from dagster import get_dagster_logger
from dagster_shared.record import IHaveNew, record_custom

logger = get_dagster_logger()


def load_yaml(path: Path) -> Mapping[str, Any]:
    """Load YAML file with error handling."""
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Warning: Could not load {path}: {e}")
        return {}


@record_custom
class DatabricksConfigs(IHaveNew):
    databricks_configs_path: Path
    all_tasks: list[Any]
    all_job_level_parameters: list[Any]

    def __new__(
        cls,
        databricks_configs_path: str,
    ) -> "DatabricksConfigs":
        databricks_configs_path = Path(databricks_configs_path)
        if not databricks_configs_path.exists():
            raise FileNotFoundError(f"Databricks config file not found: {databricks_configs_path}")

        # Load databricks config
        databricks_config = load_yaml(databricks_configs_path)
        bundle_dir = databricks_configs_path.parent

        # Extract variables and includes
        includes = databricks_config.get("include", [])

        # Parse all included resource files
        all_tasks = []
        all_job_level_parameters = {}
        for include_path in includes:
            resource_path = bundle_dir / include_path
            if resource_path.exists():
                tasks, job_level_parameters = cls._extract_tasks_from_resource(resource_path)
                all_tasks.extend(tasks)
                all_job_level_parameters.update(job_level_parameters)

        if not all_tasks:
            raise ValueError(f"No tasks found in databricks config: {databricks_configs_path}")

        return super().__new__(
            cls,
            databricks_configs_path=databricks_configs_path,
        )

    @classmethod
    def _extract_tasks_from_resource(
        cls, resource_path: Path
    ) -> tuple[list[Any], Optional[Mapping[str, Any]]]:
        """Extract Databricks tasks from a resource YAML file."""
        resource_config = load_yaml(resource_path)
        tasks = []
        job_level_parameters = {}  # Collect job-level parameters from all jobs

        # Navigate to jobs section
        resources = resource_config.get("resources", {})
        jobs = resources.get("jobs", {})

        for job_name, job_config in jobs.items():
            # Extract job-level parameters for this job
            job_params = cls._extract_job_level_parameters(job_config)
            if job_params:
                job_level_parameters[job_name] = job_params

            job_tasks = job_config.get("tasks", [])

            for job_task_config in job_tasks:
                task_key = job_task_config.get("task_key", "")
                if not task_key:
                    continue

        return tasks, job_level_parameters

    @classmethod
    def _extract_job_level_parameters(
        cls, job_config: Mapping[str, Any]
    ) -> Optional[Mapping[str, Any]]:
        """Extract job-level parameters from job configuration."""
        # Job-level parameters can be defined in several ways in Databricks bundle
        job_parameters = None

        # Check for job-level parameters in the job configuration
        if "parameters" in job_config:
            job_parameters = job_config["parameters"]
        elif "job_parameters" in job_config:
            job_parameters = job_config["job_parameters"]

        return job_parameters
