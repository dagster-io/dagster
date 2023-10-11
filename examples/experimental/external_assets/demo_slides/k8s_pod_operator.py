KubernetesPodOperator(
    image="asset-materialization-image:latest",
    # Custom CLI app to pass contextual information
    cmds=["python", "create_asset.py", "--execution-date", "{{ ds }}"],
    name="asset-materialization-pod",
    task_id="asset-materialization-task",
    in_cluster=False,
    cluster_context="kind-kind",
    config_file="/opt/airflow/.kube/config",
    is_delete_operator_pod=True,
    get_logs=True,
    # If xcom_push is True, the content of the file
    # /airflow/xcom/return.json in the container
    # will also be pushed to an XCom when the container completes.
    xcom_push=True,
)
