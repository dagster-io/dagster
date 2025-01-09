from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from airflow import DAG


def get_airflow_dags_folder() -> Path:
    # Keep import within fxn to ensure that we perform necessary verification steps first.
    from airflow.configuration import conf

    return Path(conf.get("core", "dags_folder"))


def get_all_dags() -> Mapping[str, "DAG"]:
    from airflow.models import DagBag

    return DagBag().dags


def scaffold_proxied_state(logger: Any) -> None:
    """Scaffolds a proxied state folder for the current Airflow installation.
    Each proxied state is marked as False.
    """
    proxied_state_dir = get_airflow_dags_folder() / "proxied_state"
    if proxied_state_dir.exists():
        raise Exception(
            f"Proxied state directory already exists at {proxied_state_dir}. Please remove this directory before scaffolding."
        )
    logger.info(f"Scaffolding proxied state directory at {proxied_state_dir}")
    for dag_id, dag in get_all_dags().items():
        logger.info(f"Scaffolding proxied state for dag {dag_id}")
        proxied_state_file = proxied_state_dir / f"{dag_id}.yaml"
        proxied_state_file.parent.mkdir(parents=True, exist_ok=True)
        tasks_in_alphabetical_order = sorted(dag.tasks, key=lambda task: task.task_id)
        proxied_state = {
            "tasks": [
                {"id": task.task_id, "proxied": False} for task in tasks_in_alphabetical_order
            ]
        }
        with open(proxied_state_file, "w") as f:
            yaml.dump(proxied_state, f)
