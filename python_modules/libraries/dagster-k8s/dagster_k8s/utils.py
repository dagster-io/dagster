from dagster import check, seven
from dagster.serdes import deserialize_json_to_dagster_namedtuple

from .client import (
    DEFAULT_JOB_POD_COUNT,
    DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    DEFAULT_WAIT_TIMEOUT,
    DagsterKubernetesClient,
    WaitForPodState,
)


def retrieve_pod_logs(pod_name, namespace):
    return DagsterKubernetesClient.production_client().retrieve_pod_logs(pod_name, namespace)


def get_pod_names_in_job(job_name, namespace):
    return DagsterKubernetesClient.production_client().get_pod_names_in_job(job_name, namespace)


def delete_job(job_name, namespace):
    return DagsterKubernetesClient.production_client().delete_job(job_name, namespace)


def wait_for_job_success(
    job_name,
    namespace,
    instance=None,
    run_id=None,
    wait_timeout=DEFAULT_WAIT_TIMEOUT,
    wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    num_pods_to_wait_for=DEFAULT_JOB_POD_COUNT,
):
    return DagsterKubernetesClient.production_client().wait_for_job_success(
        job_name,
        namespace,
        instance,
        run_id,
        wait_timeout,
        wait_time_between_attempts,
        num_pods_to_wait_for,
    )


def wait_for_job(
    job_name,
    namespace,
    wait_timeout=DEFAULT_WAIT_TIMEOUT,
    wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
):
    return DagsterKubernetesClient.production_client().wait_for_job(
        job_name=job_name,
        namespace=namespace,
        wait_timeout=wait_timeout,
        wait_time_between_attempts=wait_time_between_attempts,
    )


def wait_for_pod(
    pod_name,
    namespace,
    wait_for_state=WaitForPodState.Ready,
    wait_timeout=DEFAULT_WAIT_TIMEOUT,
    wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
):
    return DagsterKubernetesClient.production_client().wait_for_pod(
        pod_name, namespace, wait_for_state, wait_timeout, wait_time_between_attempts
    )


def filter_dagster_events_from_pod_logs(log_lines):
    """
    Filters the raw log lines from a dagster-cli invocation to return only the lines containing json.

     - Log lines don't necessarily come back in order
     - Something else might log JSON
     - Docker appears to silently split very long log lines -- this is undocumented behavior

     TODO: replace with reading event logs from the DB

    """
    check.list_param(log_lines, "log_lines", str)

    coalesced_lines = []
    buffer = []
    in_split_line = False
    for line in log_lines:
        line = line.strip()
        if not in_split_line and line.startswith("{"):
            if line.endswith("}"):
                coalesced_lines.append(line)
            else:
                buffer.append(line)
                in_split_line = True
        elif in_split_line:
            buffer.append(line)
            if line.endswith("}"):  # Note: hack, this may not have been the end of the full object
                coalesced_lines.append("".join(buffer))
                buffer = []
                in_split_line = False

    events = []
    for line in coalesced_lines:
        try:
            events.append(deserialize_json_to_dagster_namedtuple(line))
        except seven.JSONDecodeError:
            pass
        except check.CheckError:
            pass

    return events
