from pathlib import Path
from typing import Dict, NamedTuple

import yaml


class TaskMigrationState(NamedTuple):
    migrated: bool


class DagMigrationState(NamedTuple):
    tasks: Dict[str, TaskMigrationState]


class AirflowMigrationState(NamedTuple):
    dags: Dict[str, DagMigrationState]

    def get_migration_state_for_task(self, dag_id: str, task_id: str) -> bool:
        return self.dags[dag_id].tasks[task_id].migrated


class MigrationStateParsingError(Exception):
    pass


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
            yaml_dict = yaml.safe_load(dag_file.read_text())
            if not isinstance(yaml_dict, dict):
                raise Exception("Expected a dictionary")
            if "tasks" not in yaml_dict:
                raise Exception("Expected a 'tasks' key in the yaml")
            task_migration_states = {}
            for task_id, task_dict in yaml_dict["tasks"].items():
                if not isinstance(task_dict, dict):
                    raise Exception("Expected a dictionary for each task")
                if "migrated" not in task_dict:
                    raise Exception("Expected a 'migrated' key in the task dictionary")
                if set(task_dict.keys()) != {"migrated"}:
                    raise Exception("Expected only a 'migrated' key in the task dictionary")
                if task_dict["migrated"] not in [True, False]:
                    raise Exception("Expected 'migrated' key to be a boolean")
                task_migration_states[task_id] = TaskMigrationState(migrated=task_dict["migrated"])
            dag_migration_states[dag_id] = DagMigrationState(tasks=task_migration_states)
    except Exception as e:
        raise MigrationStateParsingError("Error parsing migration yaml") from e
    return AirflowMigrationState(dags=dag_migration_states)
