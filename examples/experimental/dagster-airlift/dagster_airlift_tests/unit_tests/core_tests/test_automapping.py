from dagster._core.definitions.asset_dep import AssetDep
from dagster_airlift.core import (
    build_defs_from_airflow_instance as build_defs_from_airflow_instance,
)
from dagster_airlift.core.airflow_defs_data import (
    key_for_automapped_task_asset,
    make_default_dag_asset_key,
)
from dagster_airlift.core.load_defs import build_full_automapped_dags_from_airflow_instance
from dagster_airlift.test import make_instance


def test_automapped_build() -> None:
    airflow_instance = make_instance(
        dag_and_task_structure={"dag1": ["task1", "task2", "standalone"]},
        task_deps={"task1": ["task2"]},
    )
    defs = build_full_automapped_dags_from_airflow_instance(
        airflow_instance=airflow_instance,
    )

    dag1_task1 = key_for_automapped_task_asset(airflow_instance.name, "dag1", "task1")
    dag1_task2 = key_for_automapped_task_asset(airflow_instance.name, "dag1", "task2")
    dag1_standalone = key_for_automapped_task_asset(airflow_instance.name, "dag1", "standalone")

    specs = {spec.key: spec for spec in defs.get_all_asset_specs()}

    assert specs[dag1_task1].deps == []
    assert specs[dag1_task2].deps == [AssetDep(dag1_task1)]
    assert specs[dag1_standalone].deps == []

    assert make_default_dag_asset_key(airflow_instance.name, "dag1") in specs

    assert specs[dag1_task1].metadata["Dag ID"] == "dag1"
    assert specs[dag1_task1].metadata["Task ID"] == "task1"
    assert specs[dag1_task1].description == 'Automapped task in dag "dag1" with task_id "task1"'
    assert specs[dag1_task2].metadata["Dag ID"] == "dag1"
    assert specs[dag1_task2].metadata["Task ID"] == "task2"

    assert "dagster/kind/airflow" in specs[dag1_task1].tags
    assert "dagster/kind/task" in specs[dag1_task1].tags

    assert set(specs[make_default_dag_asset_key(airflow_instance.name, "dag1")].deps) == {
        AssetDep(dag1_standalone),
        AssetDep(dag1_task2),
    }
