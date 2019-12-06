import os
import time
import uuid

import yaml
from dagster_k8s.launcher import K8sRunLauncher
from kubernetes import client

from dagster.core.storage.pipeline_run import PipelineRun

DAGSTER_AIRFLOW_DOCKER_IMAGE = os.environ['DAGSTER_AIRFLOW_DOCKER_IMAGE']

EXPECTED_JOB_SPEC = '''
api_version: batch/v1
kind: Job
metadata:
  labels:
    app.kubernetes.io/instance: dagster
    app.kubernetes.io/name: dagster
    app.kubernetes.io/version: 0.6.6
  name: dagster-job-{run_id}
spec:
  backoff_limit: 4
  template:
    metadata:
      labels:
        app.kubernetes.io/instance: dagster
        app.kubernetes.io/name: dagster
        app.kubernetes.io/version: 0.6.6
      name: dagster-job-pod-{run_id}
    spec:
      containers:
      - args:
        - -p
        - startPipelineExecution
        - -v
        - '{{"executionParams": {{"environmentConfigData": {{}}, "mode": "default", "selector":
          {{"name": "many_events", "solidSubset": null}}}}}}'
        command:
        - dagster-graphql
        env:
        - name: DAGSTER_HOME
          value: /opt/dagster/dagster_home
        image: {job_image}
        image_pull_policy: IfNotPresent
        name: dagster-job-{run_id}
        volume_mounts:
        - mount_path: /opt/dagster/dagster_home/dagster.yaml
          name: dagster-instance
          sub_path: dagster.yaml
      image_pull_secrets:
      - name: element-dev-key
      init_containers:
      - command:
        - sh
        - -c
        - until pg_isready -h dagster-postgresql -p 5432; do echo waiting for database;
          sleep 2; done;
        image: postgres:9.6.16
        name: check-db-ready
      restart_policy: Never
      service_account_name: dagit-admin
      volumes:
      - config_map:
          name: dagster-instance
        name: dagster-instance
'''


def remove_none(obj):
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(remove_none(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)(
            (remove_none(k), remove_none(v))
            for k, v in obj.items()
            if k is not None and v is not None
        )
    else:
        return obj


def test_k8s_run_launcher():
    run_id = uuid.uuid4().hex
    run = PipelineRun.create_empty_run('many_events', run_id, {})
    run_launcher = K8sRunLauncher(
        postgres_host='dagster-postgresql',
        postgres_port='5432',
        image_pull_secrets=[{'name': 'element-dev-key'}],
        service_account_name='dagit-admin',
        job_image=DAGSTER_AIRFLOW_DOCKER_IMAGE,
        load_kubeconfig=True,
    )
    job = run_launcher.construct_job(run)

    assert (
        yaml.dump(remove_none(job.to_dict()), default_flow_style=False).strip()
        == EXPECTED_JOB_SPEC.format(run_id=run_id, job_image=DAGSTER_AIRFLOW_DOCKER_IMAGE).strip()
    )

    run_launcher.launch_run(run)

    # Poll the job for successful completion (time out after 10 mins)
    succeeded = None
    num_iter, max_iter = 0, 20
    while succeeded is None and num_iter < max_iter:
        res = client.BatchV1Api().list_namespaced_job(namespace='default', watch=False)

        launched_job = None
        for job in res.items:
            if job.metadata.name == 'dagster-job-%s' % run_id:
                launched_job = job
                break

        # Ensure we found the job that we launched
        if launched_job is None:
            print('Job not yet launched, waiting')
            time.sleep(30)
            continue
        else:
            succeeded = launched_job.status.succeeded
            num_iter += 1
            time.sleep(30)
    assert succeeded == 1
