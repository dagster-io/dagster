import os

import yaml
from dagster import __version__ as dagster_version
from dagster.core.definitions.utils import validate_tags
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.test_utils import create_run_for_test, remove_none_recursively
from dagster.utils import load_yaml_from_path
from dagster_k8s import construct_dagster_k8s_job
from dagster_k8s.job import (
    K8S_RESOURCE_REQUIREMENTS_KEY,
    USER_DEFINED_K8S_CONFIG_KEY,
    get_user_defined_k8s_config,
)
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_workspace_and_external_pipeline,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


ENV_FROM = (
    """env_from:
        - config_map_ref:
            name: dagster-pipeline-env
        - config_map_ref:
            name: test-env-configmap
        - secret_ref:
            name: test-env-secret"""
    if IS_BUILDKITE
    else """env_from:
        - config_map_ref:
            name: dagster-pipeline-env
        - config_map_ref:
            name: test-env-configmap
        - config_map_ref:
            name: test-aws-env-configmap
        - secret_ref:
            name: test-env-secret"""
)

EXPECTED_JOB_SPEC = """
api_version: batch/v1
kind: Job
metadata:
  labels:
    app.kubernetes.io/component: run_coordinator
    app.kubernetes.io/instance: dagster
    app.kubernetes.io/name: dagster
    app.kubernetes.io/part-of: dagster
    app.kubernetes.io/version: {dagster_version}
  name: dagster-run-{run_id}
spec:
  backoff_limit: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/component: run_coordinator
        app.kubernetes.io/instance: dagster
        app.kubernetes.io/name: dagster
        app.kubernetes.io/part-of: dagster
        app.kubernetes.io/version: {dagster_version}
      name: dagster-run-{run_id}
    spec:
      containers:
      - args:
        - dagster
        - api
        - execute_run
        env:
        - name: DAGSTER_HOME
          value: /opt/dagster/dagster_home
        - name: DAGSTER_PG_PASSWORD
          value_from:
            secret_key_ref:
              key: postgresql-password
              name: dagster-postgresql-secret
        {env_from}
        image: {job_image}
        image_pull_policy: {image_pull_policy}
        name: dagster-run-{run_id}{resources}
        volume_mounts:
        - mount_path: /opt/dagster/dagster_home/dagster.yaml
          name: dagster-instance
          sub_path: dagster.yaml
        - mount_path: /opt/dagster/test_mount_path/volume_mounted_file.yaml
          name: test-volume
          sub_path: volume_mounted_file.yaml
      image_pull_secrets:
      - name: test-image-pull-secret
      restart_policy: Never
      service_account_name: dagit-admin
      volumes:
      - config_map:
          name: dagster-instance
        name: dagster-instance
      - config_map:
          name: test-volume-configmap
        name: test-volume
  ttl_seconds_after_finished: 86400
"""

EXPECTED_CONFIGURED_JOB_SPEC = """
api_version: batch/v1
kind: Job
metadata:
  labels:
    app.kubernetes.io/component: run_coordinator
    app.kubernetes.io/instance: dagster
    app.kubernetes.io/name: dagster
    app.kubernetes.io/part-of: dagster
    app.kubernetes.io/version: {dagster_version}
  name: dagster-run-{run_id}
spec:
  backoff_limit: {backoff_limit}
  template:
    metadata:
      {annotations}
      labels:
        app.kubernetes.io/component: run_coordinator
        app.kubernetes.io/instance: dagster
        app.kubernetes.io/name: dagster
        app.kubernetes.io/part-of: dagster
        app.kubernetes.io/version: {dagster_version}
        {labels}
      name: dagster-run-{run_id}
    spec:
      {affinity}
      containers:
      - args:
        - dagster
        - api
        - execute_run
        env:
        - name: DAGSTER_HOME
          value: /opt/dagster/dagster_home
        - name: DAGSTER_PG_PASSWORD
          value_from:
            secret_key_ref:
              key: postgresql-password
              name: dagster-postgresql-secret
        {env_from}
        image: {job_image}
        image_pull_policy: {image_pull_policy}
        name: dagster-run-{run_id}{resources}
        volume_mounts:
        - mount_path: /opt/dagster/dagster_home/dagster.yaml
          name: dagster-instance
          sub_path: dagster.yaml
        - mount_path: /opt/dagster/test_mount_path/volume_mounted_file.yaml
          name: test-volume
          sub_path: volume_mounted_file.yaml
      image_pull_secrets:
      - name: test-image-pull-secret
      restart_policy: Never
      service_account_name: dagit-admin
      volumes:
      - config_map:
          name: dagster-instance
        name: dagster-instance
      - config_map:
          name: test-volume-configmap
        name: test-volume
  ttl_seconds_after_finished: {ttl_seconds_after_finished}
"""


def test_valid_job_format(run_launcher):
    docker_image = get_test_project_docker_image()

    run_config = load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml"))
    pipeline_name = "demo_pipeline"
    run = PipelineRun(pipeline_name=pipeline_name, run_config=run_config)

    job_name = "dagster-run-%s" % run.run_id
    pod_name = "dagster-run-%s" % run.run_id
    job = construct_dagster_k8s_job(
        job_config=run_launcher.get_static_job_config(),
        args=["dagster", "api", "execute_run"],
        job_name=job_name,
        pod_name=pod_name,
        component="run_coordinator",
    )

    assert (
        yaml.dump(remove_none_recursively(job.to_dict()), default_flow_style=False).strip()
        == EXPECTED_JOB_SPEC.format(
            run_id=run.run_id,
            job_image=docker_image,
            image_pull_policy=image_pull_policy(),
            dagster_version=dagster_version,
            resources="",
            env_from=ENV_FROM,
        ).strip()
    )


def test_valid_job_format_with_backcompat_resources(run_launcher):
    docker_image = get_test_project_docker_image()

    run_config = load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml"))
    pipeline_name = "demo_pipeline"
    run = PipelineRun(pipeline_name=pipeline_name, run_config=run_config)

    tags = validate_tags(
        {
            K8S_RESOURCE_REQUIREMENTS_KEY: (
                {
                    "requests": {"cpu": "250m", "memory": "64Mi"},
                    "limits": {"cpu": "500m", "memory": "2560Mi"},
                }
            )
        }
    )
    user_defined_k8s_config = get_user_defined_k8s_config(tags)
    job_name = "dagster-run-%s" % run.run_id
    pod_name = "dagster-run-%s" % run.run_id
    job = construct_dagster_k8s_job(
        job_config=run_launcher.get_static_job_config(),
        args=["dagster", "api", "execute_run"],
        job_name=job_name,
        user_defined_k8s_config=user_defined_k8s_config,
        pod_name=pod_name,
        component="run_coordinator",
    )

    assert (
        yaml.dump(remove_none_recursively(job.to_dict()), default_flow_style=False).strip()
        == EXPECTED_JOB_SPEC.format(
            run_id=run.run_id,
            job_image=docker_image,
            image_pull_policy=image_pull_policy(),
            dagster_version=dagster_version,
            env_from=ENV_FROM,
            resources="""
        resources:
          limits:
            cpu: 500m
            memory: 2560Mi
          requests:
            cpu: 250m
            memory: 64Mi""",
        ).strip()
    )


def test_valid_job_format_with_user_defined_k8s_config(run_launcher):
    docker_image = get_test_project_docker_image()

    run_config = load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml"))
    pipeline_name = "demo_pipeline"
    run = PipelineRun(pipeline_name=pipeline_name, run_config=run_config)

    backoff_limit = 1234
    ttl_seconds_after_finished = 5678

    tags = validate_tags(
        {
            USER_DEFINED_K8S_CONFIG_KEY: (
                {
                    "container_config": {
                        "resources": {
                            "requests": {"cpu": "250m", "memory": "64Mi"},
                            "limits": {"cpu": "500m", "memory": "2560Mi"},
                        }
                    },
                    "pod_template_spec_metadata": {
                        "annotations": {"cluster-autoscaler.kubernetes.io/safe-to-evict": "true"},
                        "labels": {"spotinst.io/restrict-scale-down": "true"},
                    },
                    "job_spec_config": {
                        "ttl_seconds_after_finished": ttl_seconds_after_finished,
                        "backoff_limit": backoff_limit,
                    },
                    "pod_spec_config": {
                        "affinity": {
                            "nodeAffinity": {
                                "requiredDuringSchedulingIgnoredDuringExecution": {
                                    "nodeSelectorTerms": [
                                        {
                                            "matchExpressions": [
                                                {
                                                    "key": "kubernetes.io/e2e-az-name",
                                                    "operator": "In",
                                                    "values": ["e2e-az1", "e2e-az2"],
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    },
                }
            )
        }
    )
    user_defined_k8s_config = get_user_defined_k8s_config(tags)
    job_name = "dagster-run-%s" % run.run_id
    pod_name = "dagster-run-%s" % run.run_id
    job = construct_dagster_k8s_job(
        job_config=run_launcher.get_static_job_config(),
        args=["dagster", "api", "execute_run"],
        job_name=job_name,
        user_defined_k8s_config=user_defined_k8s_config,
        pod_name=pod_name,
        component="run_coordinator",
    )

    assert (
        yaml.dump(remove_none_recursively(job.to_dict()), default_flow_style=False).strip()
        == EXPECTED_CONFIGURED_JOB_SPEC.format(
            run_id=run.run_id,
            job_image=docker_image,
            image_pull_policy=image_pull_policy(),
            dagster_version=dagster_version,
            labels="spotinst.io/restrict-scale-down: 'true'",
            env_from=ENV_FROM,
            backoff_limit=backoff_limit,
            ttl_seconds_after_finished=ttl_seconds_after_finished,
            resources="""
        resources:
          limits:
            cpu: 500m
            memory: 2560Mi
          requests:
            cpu: 250m
            memory: 64Mi""",
            annotations="""annotations:
        cluster-autoscaler.kubernetes.io/safe-to-evict: \'true\'""",
            affinity="""affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/e2e-az-name
                operator: In
                values:
                - e2e-az1
                - e2e-az2""",
        ).strip()
    )


def test_k8s_run_launcher(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher
):
    run_config = load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml"))
    pipeline_name = "demo_pipeline"
    with get_test_project_workspace_and_external_pipeline(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)
        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            mode="default",
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )

        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)
        result = wait_for_job_and_get_raw_logs(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )

        assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)


def test_failing_k8s_run_launcher(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher
):
    run_config = {"blah blah this is wrong": {}}
    pipeline_name = "demo_pipeline"
    with get_test_project_workspace_and_external_pipeline(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)

        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )

        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)
        result = wait_for_job_and_get_raw_logs(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )

        assert "PIPELINE_SUCCESS" not in result, "no match, result: {}".format(result)

        event_records = dagster_instance_for_k8s_run_launcher.all_logs(run.run_id)

        assert any(
            [
                'Received unexpected config entry "blah blah this is wrong"' in str(event)
                for event in event_records
            ]
        )
        assert any(
            ['Missing required config entry "solids"' in str(event) for event in event_records]
        )
