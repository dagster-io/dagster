from pathlib import Path
from typing import Dict

from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.pydantic_yaml import parse_yaml_file_to_pydantic
from pydantic import BaseModel


class TaskMigrationState(BaseModel):
    migrated: bool


class DagMigrationState(BaseModel):
    tasks: Dict[str, TaskMigrationState]


class AirflowMigrationState(BaseModel):
    dags: Dict[str, DagMigrationState]

    def get_migration_state_for_task(self, dag_id: str, task_id: str) -> bool:
        return self.dags[dag_id].tasks[task_id].migrated


def load_migration_state_from_yaml(migration_yaml_path: Path) -> AirflowMigrationState:
    # Expect migration_yaml_path to be a directory, where each file represents a dag, and each
    # file in the subdir represents a task. The dictionary each task should consist of a single bit:
    # migrated: true/false.
    dag_migration_states = {}
    try:
        for dag_file in migration_yaml_path.iterdir():
            # Check that the file is a yaml file or yml file
            if dag_file.suffix not in [".yaml", ".yml"]:
                continue
            dag_id = dag_file.stem
            dag_migration_states[dag_id] = parse_yaml_file_to_pydantic(
                DagMigrationState, dag_file.read_text(), str(dag_file)
            )
    except Exception as e:
        raise DagsterInvalidDefinitionError("Error parsing migration yaml") from e
    return AirflowMigrationState(dags=dag_migration_states)
