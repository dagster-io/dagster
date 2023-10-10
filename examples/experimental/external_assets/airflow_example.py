from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from pendulum import datetime

default_args = {
    "start_date": datetime(2023, 10, 1),
}

with DAG(dag_id="example_kubernetes_pod", schedule="@daily", default_args=default_args) as dag:
    KubernetesPodOperator(
        image="debian:stable-slim",
        cmds=["bash", "-cx"],
        arguments=["python", "create_asset.py", "{{ ds }}"],
        name="airflow-test-pod",
        task_id="asset-materialization-task",
        in_cluster=False,
        cluster_context="docker-desktop",
        config_file="/opt/airflow/.kube/config",
        is_delete_operator_pod=True,
        get_logs=True,
    )
