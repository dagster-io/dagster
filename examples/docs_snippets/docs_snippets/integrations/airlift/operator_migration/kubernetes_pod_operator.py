# type: ignore
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

k8s_hello_world = KubernetesPodOperator(
    task_id="hello_world_task",
    name="hello-world-pod",
    image="bash:latest",
    cmds=["bash", "-cx"],
    arguments=['echo "Hello World!"'],
)
