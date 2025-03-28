---
title: 'Detect and restart crashed workers with run monitoring'
sidebar_position: 500
---

Dagster can detect hanging runs and restart crashed [run workers](/guides/deploy/oss-deployment-architecture#job-execution-flow). Using run monitoring requires:

- Running the Dagster Daemon
- Enabling run monitoring in the Dagster Instance:

<CodeExample
  path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml"
  startAfter="start_run_monitoring"
  endBefore="end_run_monitoring"
/>

:::note

In Dagster+, run monitoring is always enabled and can be configured in [deployment settings](/dagster-plus/deployment/management/deployments/deployment-settings-reference)

:::

## Run start timeouts

When Dagster launches a run, the run stays in STARTING status until the run worker spins up and marks the run as STARTED. In the event that some failure causes the run worker to not spin up, the run might be stuck in STARTING status. The `start_timeout_seconds` offers a time limit for how long runs can hang in this state before being marked as failed.

## Run cancelation timeouts

When Dagster terminates a run, the run moves into CANCELING status and sends a termination signal to the run worker. When the run worker cleans up its resources, it moves into CANCELED status. In the event that some failure causes the run worker to not spin down cleanly, the run might be stuck in CANCELING status. The `cancel_timeout_seconds` offers a time limit for how long runs can hang in this state before being marked as canceled.

## General run timeouts

After a run is marked as STARTED, it may hang indefinitely for various reasons (user API errors, network issues, etc.). You can configure a maximum runtime for every run in a deployment by setting the `run_monitoring.max_runtime_seconds` field in your dagster.yaml or [Dagster+ deployment settings](/dagster-plus/deployment/management/deployments/deployment-settings-reference) to the maximum runtime in seconds. If a run exceeds this timeout and run monitoring is enabled, it will be marked as failed. The `dagster/max_runtime` tag can also be used to set a timeout in seconds on a per-run basis.

For example, to configure a maximum of 2 hours for every run in your deployment:

```yaml
run_monitoring:
  enabled: true
  max_runtime_seconds: 7200
```

or in Dagster+, add the following to your [deployment settings](/dagster-plus/deployment/management/deployments/deployment-settings-reference):

```yaml
run_monitoring:
  max_runtime_seconds: 7200
```

The below code example shows how to set a run timeout of 10 seconds on a per-job basis:

<CodeExample
  path="docs_snippets/docs_snippets/deploying/monitoring_daemon/run_timeouts.py"
  startAfter="start_timeout"
  endBefore="end_timeout"
/>

## Detecting run worker crashes

:::note

Detecting run worker crashes only works when using a run launcher other than the <PyObject section="internals" module="dagster._core.launcher" object="DefaultRunLauncher" />.

:::

It's possible for a run worker process to crash during a run. This can happen for a variety of reasons (the host it's running on could go down, it could run out of memory, etc.). Without the monitoring daemon, there are two possible outcomes, neither desirable:

- If the run worker was able to catch the interrupt, it will mark the run as failed
- If the run worker goes down without a grace period, the run could be left hanging in STARTED status

If a run worker crashes, the run it's managing can hang. The monitoring daemon can run health checks on run workers for all active runs to detect this. If a failed run worker is detected (e.g. by the K8s Job having a non-zero exit code), the run is either marked as failed or resumed (see below).

## Resuming runs after run worker crashes

This feature is currently only supported when using:

- [`K8sRunLauncher`](/api/python-api/libraries/dagster-k8s#dagster_k8s.K8sRunLauncher) with the [`k8s_job_executor`](/api/python-api/libraries/dagster-k8s#dagster_k8s.k8s_job_executor)
- [`DockerRunLauncher`](/api/python-api/libraries/dagster-docker#dagster_docker.DockerRunLauncher) with the [`docker_executor`](/api/python-api/libraries/dagster-docker#dagster_docker.docker_executor)

The monitoring daemon handles these by performing health checks on the run workers. If a failure is detected, the daemon can launch a new run worker which resumes execution of the existing run. The run worker crash will be show in the event log, and the run will continue to completion. If the run worker continues to crash, the daemon will mark the run as failed after the configured number of attempts.

To enable, set `max_resume_run_attempts` to a value greater than 0.
