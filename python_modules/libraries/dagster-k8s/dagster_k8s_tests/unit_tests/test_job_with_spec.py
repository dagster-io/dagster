from dagster_k8s.job import DagsterK8sJobConfig, construct_dagster_k8s_job

import yaml


def test_construct_job_with_spec():
    job_spec = """
    metadata: {}
    spec:
        template:
            spec:
                containers:
                - name: first
                  imagePullPolicy: Always
                - name: second
                  image: my-image
    """
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/dagster/home",
        instance_config_map="test",
        k8s_job_object=yaml.load(job_spec),
    )
    job = construct_dagster_k8s_job(cfg, ["echo", "dagsterz"], "job123")
    job_dict = job.to_dict()

    assert job_dict["spec"]["template"]["spec"]["containers"][0]["name"] == "first"
    assert job_dict["spec"]["template"]["spec"]["containers"][0]["image"] == "test/foo:latest"
    assert job_dict["spec"]["template"]["spec"]["containers"][0]["image_pull_policy"] == "Always"
    assert job_dict["spec"]["template"]["spec"]["containers"][0]["args"] == ["echo", "dagsterz"]

    assert job_dict["spec"]["template"]["spec"]["containers"][1]["name"] == "second"
    assert job_dict["spec"]["template"]["spec"]["containers"][1]["image"] == "my-image"


def test_construct_job_with_spec_with_image():
    job_spec = """
    metadata: {}
    spec:
        template:
            spec:
                containers:
                - name: first
                  imagePullPolicy: Always
                  image: my-image
                - name: second
                  image: my-image
    """
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/dagster/home",
        instance_config_map="test",
        k8s_job_object=yaml.load(job_spec),
    )
    job = construct_dagster_k8s_job(cfg, ["echo", "dagsterz"], "job123")
    job_dict = job.to_dict()

    assert job_dict["spec"]["template"]["spec"]["containers"][0]["name"] == "first"
    assert job_dict["spec"]["template"]["spec"]["containers"][0]["image"] == "my-image"
    assert job_dict["spec"]["template"]["spec"]["containers"][0]["image_pull_policy"] == "Always"
    assert job_dict["spec"]["template"]["spec"]["containers"][0]["args"] == ["echo", "dagsterz"]

    assert job_dict["spec"]["template"]["spec"]["containers"][1]["name"] == "second"
    assert job_dict["spec"]["template"]["spec"]["containers"][1]["image"] == "my-image"
