from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, Sequence, TypedDict

import yaml
from typing_extensions import NotRequired


class TaskProxiedStateDict(TypedDict):
    id: str
    proxied: bool


class DagProxiedStateDict(TypedDict):
    tasks: NotRequired[Sequence[TaskProxiedStateDict]]
    proxied: NotRequired[bool]


class TaskProxiedState(NamedTuple):
    task_id: str
    proxied: bool

    @staticmethod
    def from_dict(task_dict: TaskProxiedStateDict) -> "TaskProxiedState":
        if set(task_dict.keys()) != {"id", "proxied"}:
            raise Exception(
                f"Expected 'proxied' and 'id' keys in the task dictionary. Found keys: {task_dict.keys()}"
            )
        if task_dict["proxied"] not in [True, False]:
            raise Exception("Expected 'proxied' key to be a boolean")
        return TaskProxiedState(task_id=task_dict["id"], proxied=task_dict["proxied"])

    def to_dict(self) -> TaskProxiedStateDict:
        return {"id": self.task_id, "proxied": self.proxied}


class DagProxiedState(NamedTuple):
    tasks: Dict[str, TaskProxiedState]
    proxied: Optional[bool] = None

    @staticmethod
    def from_dict(dag_dict: Dict[str, Any]) -> "DagProxiedState":
        if "tasks" not in dag_dict and "proxied" not in dag_dict:
            raise Exception(
                f"Expected either a 'proxied' or 'tasks' key in the dag dictionary. Instead; got: {dag_dict}"
            )
        if "proxied" in dag_dict:
            return DagProxiedState(proxied=dag_dict["proxied"], tasks={})
        else:
            task_list = dag_dict["tasks"]
            task_proxied_states = {}
            for task_dict in task_list:
                task_state = TaskProxiedState.from_dict(task_dict)
                task_proxied_states[task_state.task_id] = task_state
            return DagProxiedState(tasks=task_proxied_states)

    def to_dict(self) -> DagProxiedStateDict:
        if self.proxied is not None:
            return {"proxied": self.proxied}
        return {"tasks": [task_state.to_dict() for task_state in self.tasks.values()]}

    def is_task_proxied(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        return self.tasks[task_id].proxied


class AirflowProxiedState(NamedTuple):
    dags: Dict[str, DagProxiedState]

    def get_task_proxied_state(self, *, dag_id: str, task_id: str) -> Optional[bool]:
        if dag_id not in self.dags:
            return None
        if task_id not in self.dags[dag_id].tasks:
            return None
        return self.dags[dag_id].tasks[task_id].proxied

    def dag_proxies_tasks(self, dag_id: str) -> bool:
        # I don't love this
        return self.dags.get(dag_id) is not None and bool(self.dags[dag_id].tasks)

    def dag_proxies_dag(self, dag_id: str) -> bool:
        # I don't love this (I hate bool coercion)
        return self.dags.get(dag_id) is not None and bool(self.dags[dag_id].proxied)

    def get_proxied_dict_for_dag(self, dag_id: str) -> Optional[DagProxiedStateDict]:
        proxied_state = self.dags.get(dag_id)
        if proxied_state and proxied_state.tasks:
            return proxied_state.to_dict()
        return None

    @staticmethod
    def from_dict(proxied_dict: Dict[str, Any]) -> "AirflowProxiedState":
        dags = {}
        for dag_id, dag_dict in proxied_dict.items():
            dags[dag_id] = DagProxiedState.from_dict(dag_dict)
        return AirflowProxiedState(dags=dags)


class ProxiedStateParsingError(Exception):
    pass


def load_proxied_state_from_yaml(proxied_yaml_path: Path) -> AirflowProxiedState:
    # Expect proxied_yaml_path to be a directory, where each file represents a dag, and each
    # file in the subdir represents a task. The dictionary for each task should contain two keys;
    # id: the task id, and proxied: a boolean indicating whether the task has been proxied.
    dag_proxied_states = {}
    try:
        for dag_file in proxied_yaml_path.iterdir():
            # Check that the file is a yaml file or yml file
            if dag_file.suffix not in [".yaml", ".yml"]:
                continue
            dag_id = dag_file.stem
            yaml_dict = yaml.safe_load(dag_file.read_text())
            if not isinstance(yaml_dict, dict):
                raise Exception("Expected a dictionary")
            dag_proxied_states[dag_id] = DagProxiedState.from_dict(yaml_dict)
    except Exception as e:
        raise ProxiedStateParsingError("Error parsing proxied state yaml") from e
    return AirflowProxiedState(dags=dag_proxied_states)
