from dagster_k8s import DagsterK8sJobConfig, construct_dagster_k8s_job
from dagster_k8s.job import get_user_defined_k8s_config

from docs_snippets.deploying.kubernetes.k8s_config_tag_job import my_job
from docs_snippets.deploying.kubernetes.k8s_config_tag_op import my_op


def test_k8s_tag_job():
    assert my_job
    user_defined_cfg = get_user_defined_k8s_config(my_job.tags)

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="test",
    )
    job = construct_dagster_k8s_job(
        cfg, [], "job123", user_defined_k8s_config=user_defined_cfg
    )

    assert job.to_dict()["spec"]["template"]["spec"]["containers"][0]["resources"] == {
        "requests": {"cpu": "250m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "2560Mi"},
    }


def test_k8s_tag_op():
    assert my_op
    user_defined_cfg = get_user_defined_k8s_config(my_op.tags)

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="test",
    )
    job = construct_dagster_k8s_job(
        cfg, [], "job123", user_defined_k8s_config=user_defined_cfg
    )

    assert job.to_dict()["spec"]["template"]["spec"]["containers"][0]["resources"] == {
        "requests": {"cpu": "200m", "memory": "32Mi"},
        "limits": None,
    }
