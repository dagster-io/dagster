from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from pendulum import datetime

default_args = {
    "start_date": datetime(2023, 10, 1),
}
in_cluster = False
config_file = "/opt/airflow/.kube/config"

with DAG(dag_id="example_kubernetes_pod", schedule="@daily", default_args=default_args) as dag:
    KubernetesPodOperator(
        image="debian:stable-slim",
        cmds=["bash", "-cx"],
        arguments=["echo", "10"],
        name="airflow-test-pod",
        task_id="task-one",
        in_cluster=in_cluster,  # if set to true, will look in the cluster, if false, looks for file
        cluster_context="docker-desktop",  # is ignored when in_cluster is set to True
        config_file=config_file,
        is_delete_operator_pod=True,
        get_logs=True,
    )
