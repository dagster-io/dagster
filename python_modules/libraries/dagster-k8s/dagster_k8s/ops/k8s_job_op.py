import time

import kubernetes

from dagster import Field, In, Noneable, Nothing, Permissive, StringSource, op
from dagster._annotations import experimental
from dagster._utils import merge_dicts

from ..container_context import K8sContainerContext
from ..job import (
    DagsterK8sJobConfig,
    UserDefinedDagsterK8sConfig,
    construct_dagster_k8s_job,
    get_k8s_job_name,
)
from ..launcher import K8sRunLauncher
from ..utils import (
    wait_for_job,
    wait_for_job_to_have_pods,
    wait_for_pod,
    wait_for_running_job_to_succeed,
)


@op(
    ins={"start_after": In(Nothing)},
    config_schema=merge_dicts(
        DagsterK8sJobConfig.config_type_container(),
        {
            "image": Field(
                StringSource,
                is_required=True,
                description="The image in which to launch the k8s job.",
            ),
            "command": Field(
                [str],
                is_required=False,
                description="The command to run in the container within the launched k8s job.",
            ),
            "args": Field(
                [str],
                is_required=False,
                description="The args for the command for the container.",
            ),
            "namespace": Field(StringSource, is_required=False),
            "load_incluster_config": Field(
                bool,
                is_required=False,
                default_value=True,
                description="""Set this value if you are running the launcher
            within a k8s cluster. If ``True``, we assume the launcher is running within the target
            cluster and load config using ``kubernetes.config.load_incluster_config``. Otherwise,
            we will use the k8s config specified in ``kubeconfig_file`` (using
            ``kubernetes.config.load_kube_config``) or fall back to the default kubeconfig.""",
            ),
            "kubeconfig_file": Field(
                Noneable(str),
                is_required=False,
                default_value=None,
                description="The kubeconfig file from which to load config. Defaults to using the default kubeconfig.",
            ),
            "timeout": Field(
                int,
                is_required=False,
                description="How long to wait for the job to succeed before raising an exception",
            ),
            "container_config": Field(
                Permissive(),
                is_required=False,
                description="Raw k8s config for the k8s pod's main container (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#container-v1-core). Keys can either snake_case or camelCase.",
            ),
            "pod_template_spec_metadata": Field(
                Permissive(),
                is_required=False,
                description="Raw k8s config for the k8s pod's metadata (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#objectmeta-v1-meta). Keys can either snake_case or camelCase.",
            ),
            "pod_spec_config": Field(
                Permissive(),
                is_required=False,
                description="Raw k8s config for the k8s pod's pod spec (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#podspec-v1-core). Keys can either snake_case or camelCase.",
            ),
            "job_metadata": Field(
                Permissive(),
                is_required=False,
                description="Raw k8s config for the k8s job's metadata (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#objectmeta-v1-meta). Keys can either snake_case or camelCase.",
            ),
            "job_spec_config": Field(
                Permissive(),
                is_required=False,
                description="Raw k8s config for the k8s job's job spec (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#jobspec-v1-batch). Keys can either snake_case or camelCase.",
            ),
        },
    ),
)
@experimental
def k8s_job_op(context):
    """
    An op that runs a Kubernetes job using the k8s API.

    Contrast with the `k8s_job_executor`, which runs each Dagster op in a Dagster job in its
    own k8s job.

    This op may be useful when:
      - You need to orchestrate a command that isn't a Dagster op (or isn't written in Python)
      - You want to run the rest of a Dagster job using a specific executor, and only a single
        op in k8s.

    For example:

    .. literalinclude:: ../../../../../../python_modules/libraries/dagster-k8s/dagster_k8s_tests/unit_tests/test_example_k8s_job_op.py
      :start-after: start_marker
      :end-before: end_marker
      :language: python

    The service account that is used to run this job should have the following RBAC permissions:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/kubernetes/k8s_job_op_rbac.yaml
       :language: YAML
    """

    config = context.op_config

    run_container_context = K8sContainerContext.create_for_run(
        context.pipeline_run,
        context.instance.run_launcher
        if isinstance(context.instance.run_launcher, K8sRunLauncher)
        else None,
    )

    op_container_context = K8sContainerContext(
        image_pull_policy=config.get("image_pull_policy"),  # type: ignore
        image_pull_secrets=config.get("image_pull_secrets"),  # type: ignore
        service_account_name=config.get("service_account_name"),  # type: ignore
        env_config_maps=config.get("env_config_maps"),  # type: ignore
        env_secrets=config.get("env_secrets"),  # type: ignore
        env_vars=config.get("env_vars"),  # type: ignore
        volume_mounts=config.get("volume_mounts"),  # type: ignore
        volumes=config.get("volumes"),  # type: ignore
        labels=config.get("labels"),  # type: ignore
        namespace=config.get("namespace"),  # type: ignore
        resources=config.get("resources"),  # type: ignore
    )

    container_context = run_container_context.merge(op_container_context)

    namespace = container_context.namespace

    container_config = config.get("container_config", {})
    command = config.get("command")
    if command:
        container_config["command"] = command

    user_defined_k8s_config = UserDefinedDagsterK8sConfig(
        container_config=container_config,
        pod_template_spec_metadata=config.get("pod_template_spec_metadata"),
        pod_spec_config=config.get("pod_spec_config"),
        job_metadata=config.get("job_metadata"),
        job_spec_config=config.get("job_spec_config"),
    )

    k8s_job_config = DagsterK8sJobConfig(
        job_image=config["image"],
        dagster_home=None,
        image_pull_policy=container_context.image_pull_policy,
        image_pull_secrets=container_context.image_pull_secrets,
        service_account_name=container_context.service_account_name,
        instance_config_map=None,
        postgres_password_secret=None,
        env_config_maps=container_context.env_config_maps,
        env_secrets=container_context.env_secrets,
        env_vars=container_context.env_vars,
        volume_mounts=container_context.volume_mounts,
        volumes=container_context.volumes,
        labels=container_context.labels,
        resources=container_context.resources,
    )

    job_name = get_k8s_job_name(context.run_id, context.op.name)

    job = construct_dagster_k8s_job(
        job_config=k8s_job_config,
        args=config.get("args"),
        job_name=job_name,
        pod_name=job_name,
        component="k8s_job_op",
        user_defined_k8s_config=user_defined_k8s_config,
        labels={
            "dagster/job": context.pipeline_run.pipeline_name,
            "dagster/op": context.op.name,
            "dagster/run-id": context.pipeline_run.run_id,
        },
    )

    if config["load_incluster_config"]:
        kubernetes.config.load_incluster_config()
    else:
        kubernetes.config.load_kube_config(config.get("kubeconfig_file"))

    context.log.info(f"Creating Kubernetes job {job_name} in namespace {namespace}...")

    start_time = time.time()

    kubernetes.client.BatchV1Api().create_namespaced_job(namespace, job)

    core_api = kubernetes.client.CoreV1Api()

    context.log.info("Waiting for Kubernetes job to finish...")

    timeout = config.get("timeout", 0)

    wait_for_job(
        job_name=job_name,
        namespace=namespace,
        wait_timeout=timeout,
        start_time=start_time,
    )

    pods = wait_for_job_to_have_pods(
        job_name,
        namespace,
        wait_timeout=timeout,
        start_time=start_time,
    )

    pod_names = [p.metadata.name for p in pods]

    if not pod_names:
        raise Exception("No pod names in job after it started")

    pod_to_watch = pod_names[0]
    watch = kubernetes.watch.Watch()

    wait_for_pod(pod_to_watch, namespace, wait_timeout=timeout, start_time=start_time)

    log_stream = watch.stream(
        core_api.read_namespaced_pod_log, name=pod_to_watch, namespace=namespace
    )

    while True:
        if timeout and time.time() - start_time > timeout:
            watch.stop()
            raise Exception("Timed out waiting for pod to finish")

        try:
            log_entry = next(log_stream)
            print(log_entry)  # pylint: disable=print-call
        except StopIteration:
            break

    wait_for_running_job_to_succeed(
        job_name=job_name,
        namespace=namespace,
        wait_timeout=timeout,
        start_time=start_time,
    )
