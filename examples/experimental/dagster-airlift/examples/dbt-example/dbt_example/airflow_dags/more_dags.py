from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.migration_state import load_migration_state_from_yaml

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG("kubernetes_sample", default_args=default_args, schedule_interval=timedelta(days=1))

kubernetes_min_pod = KubernetesPodOperator(
    task_id="k8s_test_task",
    name="airflow-test-pod",
    namespace="default",
    image="ubuntu:18.04",
    cmds=["bash", "-cx"],
    arguments=["echo", "hello world"],
    labels={"foo": "bar"},
    dag=dag,
    is_delete_operator_pod=True,
    in_cluster=False,
    cluster_context="minikube",
)

mark_as_dagster_migrating(
    global_vars=globals(),
    migration_state=load_migration_state_from_yaml(Path(__file__).parent / "migration_state"),
)
