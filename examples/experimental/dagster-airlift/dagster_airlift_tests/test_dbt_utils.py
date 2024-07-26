import os
from typing import Sequence

from dagster import AssetKey
from dagster_airlift import TaskMapping, airflow_task_mappings_from_dbt_project


def test_task_mappings(dbt_project_dir: str, dbt_project: None) -> None:
    """Test that DBT project is correctly parsed as airflow tasks."""
    dbt_manifest_path = os.path.join(dbt_project_dir, "target", "manifest.json")
    airflow_instance_name = "airflow_instance"
    dag_id = "dag_id"
    task_id = "task_id"
    mappings: Sequence[TaskMapping] = airflow_task_mappings_from_dbt_project(
        dbt_manifest_path=dbt_manifest_path,
        airflow_instance_name=airflow_instance_name,
        dag_id=dag_id,
        task_id=task_id,
    )
    # In jaffle shop, there are 8 dbt models.
    # raw versionsof payments, orders, and customers, staging versions of payments, orders, and
    # customers, and final versions of orders, and customers. We expect this to be reflected in the
    # mappings.
    assert len(mappings) == 8
    expected_table_names = {
        "raw_customers": [],
        "raw_orders": [],
        "raw_payments": [],
        "stg_customers": ["raw_customers"],
        "stg_orders": ["raw_orders"],
        "stg_payments": ["raw_payments"],
        "orders": ["stg_orders", "stg_payments"],
        "customers": ["stg_customers", "stg_orders", "stg_payments"],
    }
    expected_prefix = ["airflow_instance", "dbt"]
    # assert expected asset keys.
    assert {mapping.key for mapping in mappings} == {
        AssetKey(expected_prefix + [table_name]) for table_name in expected_table_names.keys()
    }
    # assert expected deps.
    for mapping in mappings:
        assert {dep.asset_key for dep in mapping.deps} == {
            AssetKey(expected_prefix + [dep_table_name])
            for dep_table_name in expected_table_names[mapping.key.path[-1]]
        }, f"Deps don't match for {mapping.key.path[-1]}"
        assert mapping.task_id == task_id
        assert mapping.dag_id == dag_id
