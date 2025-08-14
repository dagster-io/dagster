from collections.abc import Mapping
from functools import cached_property
from pathlib import Path
from typing import Any, Optional, Union

import yaml
from dagster import get_dagster_logger
from dagster_shared.record import IHaveNew, record, record_custom

logger = get_dagster_logger()


def load_yaml(path: Path) -> Mapping[str, Any]:
    """Load YAML file with error handling."""
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Warning: Could not load {path}: {e}")
        return {}


def parse_depends_on(depends_on: Optional[list]) -> list[str]:
    parsed_depends_on = []
    if depends_on:
        for dep in depends_on:
            if isinstance(dep, dict) and "task_key" in dep:
                parsed_depends_on.append(dep["task_key"])
            elif isinstance(dep, str):
                parsed_depends_on.append(dep)
    return parsed_depends_on


@record
class DatabricksNotebookTask:
    task_key: str
    task_config: Mapping[str, Any]
    task_parameters: Mapping[str, Any]
    depends_on: list[str]
    job_name: str
    libraries: list[Mapping[str, Any]]

    @property
    def task_type(self) -> str:
        return "notebook"

    @cached_property
    def task_config_metadata(self) -> Mapping[str, Any]:
        task_config_metadata = {}
        notebook_task = self.task_config["notebook_task"]
        task_config_metadata["notebook_path"] = notebook_task.get("notebook_path", "")
        task_config_metadata["parameters"] = self.task_parameters
        return task_config_metadata

    @classmethod
    def from_job_task_config(cls, job_task_config: Mapping[str, Any]) -> "DatabricksNotebookTask":
        notebook_task = job_task_config["notebook_task"]
        task_config = {"notebook_task": notebook_task}
        task_parameters = notebook_task.get("base_parameters", {})
        return cls(
            task_key=job_task_config["task_key"],
            task_config=task_config,
            task_parameters=task_parameters,
            depends_on=parse_depends_on(job_task_config.get("depends_on", [])),
            job_name=job_task_config["job_name"],
            libraries=job_task_config.get("libraries", []),
        )


@record
class DatabricksConditionTask:
    task_key: str
    task_config: Mapping[str, Any]
    task_parameters: Mapping[str, Any]
    depends_on: list[str]
    job_name: str
    libraries: list[Mapping[str, Any]]

    @property
    def task_type(self) -> str:
        return "condition"

    @cached_property
    def task_config_metadata(self) -> Mapping[str, Any]:
        task_config_metadata = {}
        condition_config = self.task_config["condition_task"]
        task_config_metadata["left"] = condition_config.get("left", "")
        task_config_metadata["op"] = condition_config.get("op", "EQUAL_TO")
        task_config_metadata["right"] = condition_config.get("right", "")
        return task_config_metadata

    @classmethod
    def from_job_task_config(cls, job_task_config: Mapping[str, Any]) -> "DatabricksConditionTask":
        condition_task = job_task_config["condition_task"]
        task_config = {"condition_task": condition_task}
        # Condition tasks don't have traditional parameters
        task_parameters = {}
        return cls(
            task_key=job_task_config["task_key"],
            task_config=task_config,
            task_parameters=task_parameters,
            depends_on=parse_depends_on(job_task_config.get("depends_on", [])),
            job_name=job_task_config["job_name"],
            libraries=job_task_config.get("libraries", []),
        )


@record_custom
class DatabricksConfigs(IHaveNew):
    databricks_configs_path: Path
    tasks: list[Any]
    job_level_parameters: Mapping[str, Any]

    def __new__(
        cls,
        databricks_configs_path: Union[Path, str],
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
        tasks = []
        job_level_parameters = {}
        for include_path in includes:
            resource_path = bundle_dir / include_path
            if resource_path.exists():
                resource_tasks, resource_job_level_parameters = cls._extract_tasks_from_resource(
                    resource_path
                )
                tasks.extend(resource_tasks)
                if resource_job_level_parameters:
                    job_level_parameters.update(resource_job_level_parameters)

        if not tasks:
            raise ValueError(f"No tasks found in databricks config: {databricks_configs_path}")

        return super().__new__(
            cls,
            databricks_configs_path=databricks_configs_path,
            tasks=tasks,
            job_level_parameters=job_level_parameters,
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

                augmented_job_task_config = {**job_task_config, "job_name": job_name}

                if "notebook_task" in job_task_config:
                    tasks.append(
                        DatabricksNotebookTask.from_job_task_config(
                            job_task_config=augmented_job_task_config
                        )
                    )
                elif "condition_task" in job_task_config:
                    tasks.append(
                        DatabricksConditionTask.from_job_task_config(
                            job_task_config=augmented_job_task_config
                        )
                    )

                else:
                    # Skip unknown task types
                    logger.warning(f"Warning: Unknown task type for task {task_key}, skipping")
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
