# pyright: reportUnusedExpression=none

from airflow import models
from airflow.operators.dummy_operator import DummyOperator  # type: ignore
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.utils.dates import days_ago

default_args = {"start_date": days_ago(1)}

with models.DAG(
    dag_id="kubernetes_dag", default_args=default_args, schedule_interval=None
) as kubernetes_dag:
    run_this_last = DummyOperator(
        task_id="sink_task_1",
        dag=kubernetes_dag,
    )

    k = KubernetesPodOperator(
        name="hello-dry-run",
        # will need to modified to match your k8s context
        cluster_context="hooli-user-cluster",
        namespace="default",
        image="debian",
        cmds=["bash", "-cx"],
        arguments=["echo", "10"],
        labels={"foo": "bar"},
        task_id="dry_run_demo",
        do_xcom_push=True,
    )
    k >> run_this_last
