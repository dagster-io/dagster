from dagster_airlift.in_airflow.task_proxy_operator import matched_dag_id_task_id


def test_parse_asset_node() -> None:
    asset_node = {
        "id": 'dbt_example.dagster_defs.migrate.__repository__.["lakehouse", "iris"]',
        "assetKey": {"path": ["lakehouse", "iris"]},
        "metadataEntries": [
            {
                "label": "dagster-airlift/task-mapping",
                "jsonString": '[{"dag_id": "rebuild_iris_models", "task_id": "load_iris"}]',
                "__typename": "JsonMetadataEntry",
            },
            {
                "label": "Task Info (raw)",
                "jsonString": '{"class_ref": {"class_name": "DefaultProxyToDagsterOperator", "module_path": "dagster_airlift.in_airflow.base_proxy_operator"}, "depends_on_past": false, "downstream_task_ids": ["build_dbt_models"], "end_date": null, "execution_timeout": null, "extra_links": [], "is_mapped": false, "operator_name": "DefaultProxyToDagsterOperator", "owner": "airflow", "params": {}, "pool": "default_pool", "pool_slots": 1.0, "priority_weight": 1.0, "queue": "default", "retries": 0.0, "retry_delay": {"__type": "TimeDelta", "days": 0, "microseconds": 0, "seconds": 300}, "retry_exponential_backoff": false, "start_date": "2024-09-24T18:48:05.148806+00:00", "task_id": "load_iris", "template_fields": [], "trigger_rule": "all_success", "ui_color": "#fff", "ui_fgcolor": "#000", "wait_for_downstream": false, "weight_rule": "downstream"}',
                "__typename": "JsonMetadataEntry",
            },
            {"label": "Dag ID", "text": "rebuild_iris_models", "__typename": "TextMetadataEntry"},
            {"__typename": "UrlMetadataEntry"},
            {
                "label": "Triggered by Task ID",
                "text": "load_iris",
                "__typename": "TextMetadataEntry",
            },
        ],
        "jobs": [
            {
                "id": "50b0b23cdb52e8f68e39bce56dd28e30ef221a53",
                "name": "__ASSET_JOB",
                "repository": {
                    "id": "0abb753321e78ef093132df5e05aa2046ce7bca9::7170e8bbd3d71e16435c1fbdad3185ab83074660",
                    "name": "__repository__",
                    "location": {
                        "id": "dbt_example.dagster_defs.migrate",
                        "name": "dbt_example.dagster_defs.migrate",
                    },
                },
            }
        ],
    }
    assert matched_dag_id_task_id(asset_node, "rebuild_iris_models", "load_iris")
    assert not matched_dag_id_task_id(asset_node, "other_dag", "other_task")
