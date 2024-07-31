from pathlib import Path
from typing import Dict

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
    # Expect migration_yaml_path to be a directory, where each subdir represents a dag, and each
    # file in the subdir represents a task. The file for each task should consist of a single bit:
    # migrated: true/false.
    # The task_id can be inferred from the filename.
    dags = {}
    for dag_dir in migration_yaml_path.iterdir():
        if not dag_dir.is_dir():
            continue
        tasks = {}
        for task_file in dag_dir.iterdir():
            if not task_file.is_file():
                continue
            task_id = task_file.stem
            # make sure to remove extensions from the file name
            task_state = parse_yaml_file_to_pydantic(TaskMigrationState, task_file.read_text())
            tasks[task_id] = task_state
        dags[dag_dir.name] = DagMigrationState(tasks=tasks)
    return AirflowMigrationState(dags=dags)
