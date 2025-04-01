import os
import time
from typing import Any, Optional

import kubernetes.config
import kubernetes.watch
from dagster import (
    Enum as DagsterEnum,
    Field,
    In,
    Noneable,
    Nothing,
    OpExecutionContext,
    Permissive,
    StringSource,
    op,
)
from dagster._annotations import beta
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._utils.merger import merge_dicts

from dagster_k8s.client import DEFAULT_JOB_POD_COUNT, DagsterKubernetesClient, k8s_api_retry
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.job import (
    DagsterK8sJobConfig,
    K8sConfigMergeBehavior,
    UserDefinedDagsterK8sConfig,
    construct_dagster_k8s_job,
    get_k8s_job_name,
)
from dagster_k8s.launcher import K8sRunLauncher

K8S_JOB_OP_CONFIG = merge_dicts(
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
            description=(
                "The kubeconfig file from which to load config. Defaults to using the default"
                " kubeconfig."
            ),
        ),
        "timeout": Field(
            int,
            is_required=False,
            description="How long to wait for the job to succeed before raising an exception",
        ),
        "container_config": Field(
            Permissive(),
            is_required=False,
            description=(
                "Raw k8s config for the k8s pod's main container"
                " (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.30/#container-v1-core)."
                " Keys can either snake_case or camelCase."
            ),
        ),
        "pod_template_spec_metadata": Field(
            Permissive(),
            is_required=False,
            description=(
                "Raw k8s config for the k8s pod's metadata"
                " (https://kubernetes.io/docs/reference/kubernetes-api/common-definitions/object-meta/#ObjectMeta)."
                " Keys can either snake_case or camelCase."
            ),
        ),
        "pod_spec_config": Field(
            Permissive(),
            is_required=False,
            description=(
                "Raw k8s config for the k8s pod's pod spec"
                " (https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#PodSpec)."
                " Keys can either snake_case or camelCase."
            ),
        ),
        "job_metadata": Field(
            Permissive(),
            is_required=False,
            description=(
                "Raw k8s config for the k8s job's metadata"
                " (https://kubernetes.io/docs/reference/kubernetes-api/common-definitions/object-meta/#ObjectMeta)."
                " Keys can either snake_case or camelCase."
            ),
        ),
        "job_spec_config": Field(
            Permissive(),
            is_required=False,
            description=(
                "Raw k8s config for the k8s job's job spec"
                " (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.30/#jobspec-v1-batch)."
                " Keys can either snake_case or camelCase."
            ),
        ),
        "merge_behavior": Field(
            DagsterEnum.from_python_enum(K8sConfigMergeBehavior),
            is_required=False,
            default_value=K8sConfigMergeBehavior.DEEP.value,
            description=(
                "How raw k8s config set on this op should be merged with any raw k8s config set on"
                " the code location that launched the op. By default, the value is SHALLOW, meaning"
                " that the two dictionaries are shallowly merged - any shared values in the "
                " dictionaries will be replaced by the values set on this op. Setting it to DEEP"
                " will recursively merge the two dictionaries, appending list fields together and"
                " merging dictionary fields."
            ),
        ),
    },
)


@beta
def execute_k8s_job(
    context: OpExecutionContext,
    image: str,
    command: Optional[list[str]] = None,
    args: Optional[list[str]] = None,
    namespace: Optional[str] = None,
    image_pull_policy: Optional[str] = None,
    image_pull_secrets: Optional[list[dict[str, str]]] = None,
    service_account_name: Optional[str] = None,
    env_config_maps: Optional[list[str]] = None,
    env_secrets: Optional[list[str]] = None,
    env_vars: Optional[list[str]] = None,
    volume_mounts: Optional[list[dict[str, Any]]] = None,
    volumes: Optional[list[dict[str, Any]]] = None,
    labels: Optional[dict[str, str]] = None,
    resources: Optional[dict[str, Any]] = None,
    scheduler_name: Optional[str] = None,
    load_incluster_config: bool = True,
    kubeconfig_file: Optional[str] = None,
    timeout: Optional[int] = None,
    container_config: Optional[dict[str, Any]] = None,
    pod_template_spec_metadata: Optional[dict[str, Any]] = None,
    pod_spec_config: Optional[dict[str, Any]] = None,
    job_metadata: Optional[dict[str, Any]] = None,
    job_spec_config: Optional[dict[str, Any]] = None,
    k8s_job_name: Optional[str] = None,
    merge_behavior: K8sConfigMergeBehavior = K8sConfigMergeBehavior.DEEP,
    delete_failed_k8s_jobs: Optional[bool] = True,
    _kubeconfig_file_context: Optional[str] = None,
):
    """This function is a utility for executing a Kubernetes job from within a Dagster op.

    Args:
        image (str): The image in which to launch the k8s job.
        command (Optional[List[str]]): The command to run in the container within the launched
            k8s job. Default: None.
        args (Optional[List[str]]): The args for the command for the container. Default: None.
        namespace (Optional[str]): Override the kubernetes namespace in which to run the k8s job.
            Default: None.
        image_pull_policy (Optional[str]): Allows the image pull policy to be overridden, e.g. to
            facilitate local testing with `kind <https://kind.sigs.k8s.io/>`_. Default:
            ``"Always"``. See:
            https://kubernetes.io/docs/concepts/containers/images/#updating-images.
        image_pull_secrets (Optional[List[Dict[str, str]]]): Optionally, a list of dicts, each of
            which corresponds to a Kubernetes ``LocalObjectReference`` (e.g.,
            ``{'name': 'myRegistryName'}``). This allows you to specify the ```imagePullSecrets`` on
            a pod basis. Typically, these will be provided through the service account, when needed,
            and you will not need to pass this argument. See:
            https://kubernetes.io/docs/concepts/containers/images/#specifying-imagepullsecrets-on-a-pod
            and https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.17/#podspec-v1-core
        service_account_name (Optional[str]): The name of the Kubernetes service account under which
            to run the Job. Defaults to "default"        env_config_maps (Optional[List[str]]): A list of custom ConfigMapEnvSource names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
            https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container
        env_secrets (Optional[List[str]]): A list of custom Secret names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
            https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables
        env_vars (Optional[List[str]]): A list of environment variables to inject into the Job.
            Default: ``[]``. See: https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables
        volume_mounts (Optional[List[Permissive]]): A list of volume mounts to include in the job's
            container. Default: ``[]``. See:
            https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volumemount-v1-core
        volumes (Optional[List[Permissive]]): A list of volumes to include in the Job's Pod. Default: ``[]``. See:
            https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volume-v1-core
        labels (Optional[Dict[str, str]]): Additional labels that should be included in the Job's Pod. See:
            https://kubernetes.io/docs/concepts/overview/working-with-objects/labels
        resources (Optional[Dict[str, Any]]) Compute resource requirements for the container. See:
            https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
        scheduler_name (Optional[str]): Use a custom Kubernetes scheduler for launched Pods. See:
            https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/
        load_incluster_config (bool): Whether the op is running within a k8s cluster. If ``True``,
            we assume the launcher is running within the target cluster and load config using
            ``kubernetes.config.load_incluster_config``. Otherwise, we will use the k8s config
            specified in ``kubeconfig_file`` (using ``kubernetes.config.load_kube_config``) or fall
            back to the default kubeconfig. Default: True,
        kubeconfig_file (Optional[str]): The kubeconfig file from which to load config. Defaults to
            using the default kubeconfig. Default: None.
        timeout (Optional[int]): Raise an exception if the op takes longer than this timeout in
            seconds to execute. Default: None.
        container_config (Optional[Dict[str, Any]]): Raw k8s config for the k8s pod's main container
            (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.30/#container-v1-core).
            Keys can either snake_case or camelCase.Default: None.
        pod_template_spec_metadata (Optional[Dict[str, Any]]): Raw k8s config for the k8s pod's
            metadata (https://kubernetes.io/docs/reference/kubernetes-api/common-definitions/object-meta/#ObjectMeta).
            Keys can either snake_case or camelCase. Default: None.
        pod_spec_config (Optional[Dict[str, Any]]): Raw k8s config for the k8s pod's pod spec
            (https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#PodSpec).
            Keys can either snake_case or camelCase. Default: None.
        job_metadata (Optional[Dict[str, Any]]): Raw k8s config for the k8s job's metadata
            (https://kubernetes.io/docs/reference/kubernetes-api/common-definitions/object-meta/#ObjectMeta).
            Keys can either snake_case or camelCase. Default: None.
        job_spec_config (Optional[Dict[str, Any]]): Raw k8s config for the k8s job's job spec
            (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.30/#jobspec-v1-batch).
            Keys can either snake_case or camelCase.Default: None.
        k8s_job_name (Optional[str]): Overrides the name of the k8s job. If not set, will be set
            to a unique name based on the current run ID and the name of the calling op. If set,
            make sure that the passed in name is a valid Kubernetes job name that does not
            already exist in the cluster.
        merge_behavior (Optional[K8sConfigMergeBehavior]): How raw k8s config set on this op should
            be merged with any raw k8s config set on the code location that launched the op. By
            default, the value is K8sConfigMergeBehavior.DEEP, meaning that the two dictionaries
            are recursively merged, appending list fields together and merging dictionary fields.
            Setting it to SHALLOW will make the dictionaries shallowly merged - any shared values
            in the dictionaries will be replaced by the values set on this op.
        delete_failed_k8s_jobs (bool): Whether to immediately delete failed Kubernetes jobs. If False,
            failed jobs will remain accessible through the Kubernetes API until deleted by a user or cleaned up by the
            .spec.ttlSecondsAfterFinished parameter of the job.
            (https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/).
            Defaults to True.
    """
    run_container_context = K8sContainerContext.create_for_run(
        context.dagster_run,
        (
            context.instance.run_launcher
            if isinstance(context.instance.run_launcher, K8sRunLauncher)
            else None
        ),
        include_run_tags=False,
    )

    container_config = container_config.copy() if container_config else {}
    if command:
        container_config["command"] = command

    op_container_context = K8sContainerContext(
        image_pull_policy=image_pull_policy,
        image_pull_secrets=image_pull_secrets,
        service_account_name=service_account_name,
        env_config_maps=env_config_maps,
        env_secrets=env_secrets,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
        volumes=volumes,
        labels=labels,
        namespace=namespace,
        resources=resources,
        scheduler_name=scheduler_name,
        run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
            {
                "container_config": container_config,
                "pod_template_spec_metadata": pod_template_spec_metadata,
                "pod_spec_config": pod_spec_config,
                "job_metadata": job_metadata,
                "job_spec_config": job_spec_config,
                "merge_behavior": merge_behavior.value,
            }
        ),
    )

    container_context = run_container_context.merge(op_container_context)

    namespace = container_context.namespace

    user_defined_k8s_config = container_context.run_k8s_config

    k8s_job_config = DagsterK8sJobConfig(
        job_image=image,
        dagster_home=None,
    )

    job_name = k8s_job_name or get_k8s_job_name(
        context.run_id, context.get_step_execution_context().step.key
    )

    retry_number = context.retry_number
    if retry_number > 0:
        job_name = f"{job_name}-{retry_number}"

    labels = {
        "dagster/job": context.dagster_run.job_name,
        "dagster/op": context.op.name,
        "dagster/run-id": context.dagster_run.run_id,
    }
    if context.dagster_run.remote_job_origin:
        labels["dagster/code-location"] = (
            context.dagster_run.remote_job_origin.repository_origin.code_location_origin.location_name
        )

    job = construct_dagster_k8s_job(
        job_config=k8s_job_config,
        args=args,
        job_name=job_name,
        pod_name=job_name,
        component="k8s_job_op",
        user_defined_k8s_config=user_defined_k8s_config,
        labels=labels,
    )

    if load_incluster_config:
        kubernetes.config.load_incluster_config()
    else:
        kubernetes.config.load_kube_config(kubeconfig_file, context=_kubeconfig_file_context)

    # changing this to be able to be passed in will allow for unit testing
    api_client = DagsterKubernetesClient.production_client()

    context.log.info(f"Creating Kubernetes job {job_name} in namespace {namespace}...")

    start_time = time.time()

    api_client.batch_api.create_namespaced_job(namespace, job)

    context.log.info("Waiting for Kubernetes job to finish...")

    timeout = timeout or 0

    try:
        api_client.wait_for_job(
            job_name=job_name,
            namespace=namespace,
            wait_timeout=timeout,
            start_time=start_time,
        )

        restart_policy = user_defined_k8s_config.pod_spec_config.get("restart_policy", "Never")

        if restart_policy == "Never":
            container_name = container_config.get("name", "dagster")

            pods = api_client.wait_for_job_to_have_pods(
                job_name,
                namespace,
                wait_timeout=timeout,
                start_time=start_time,
            )

            pod_names = [p.metadata.name for p in pods]

            if not pod_names:
                raise Exception("No pod names in job after it started")

            pod_to_watch = pod_names[0]
            watch = kubernetes.watch.Watch()  # consider moving in to api_client

            api_client.wait_for_pod(
                pod_to_watch,
                namespace,  # pyright: ignore[reportArgumentType]
                wait_timeout=timeout,
                start_time=start_time,  # pyright: ignore[reportArgumentType]
            )

            log_stream = watch.stream(
                api_client.core_api.read_namespaced_pod_log,
                name=pod_to_watch,
                namespace=namespace,
                container=container_name,
            )

            while True:
                if timeout and time.time() - start_time > timeout:
                    watch.stop()
                    raise Exception("Timed out waiting for pod to finish")
                try:
                    log_entry = k8s_api_retry(
                        lambda: next(log_stream),
                        max_retries=int(
                            os.getenv("DAGSTER_EXECUTE_K8S_JOB_STREAM_LOGS_RETRIES", "3")
                        ),
                        timeout=int(
                            os.getenv(
                                "DAGSTER_EXECUTE_K8S_JOB_STREAM_LOGS_WAIT_BETWEEN_ATTEMPTS", "5"
                            )
                        ),
                    )
                    print(log_entry)  # noqa: T201
                except StopIteration:
                    break
                except Exception:
                    context.log.warning(
                        "Error reading pod logs. Giving up and waiting for the pod to finish",
                        exc_info=True,
                    )
                    break
        else:
            context.log.info("Pod logs are disabled, because restart_policy is not Never")

        if job_spec_config and job_spec_config.get("parallelism"):
            num_pods_to_wait_for = job_spec_config["parallelism"]
        else:
            num_pods_to_wait_for = DEFAULT_JOB_POD_COUNT

        api_client.wait_for_running_job_to_succeed(
            job_name=job_name,
            namespace=namespace,
            wait_timeout=timeout,
            start_time=start_time,
            num_pods_to_wait_for=num_pods_to_wait_for,
        )
    except (DagsterExecutionInterruptedError, Exception) as e:
        try:
            pods = api_client.get_pod_names_in_job(job_name=job_name, namespace=namespace)
            pod_debug_info = "\n\n".join(
                [api_client.get_pod_debug_info(pod_name, namespace) for pod_name in pods]
            )
        except Exception:
            context.log.exception(
                f"Error trying to get pod debug information for failed k8s job {job_name}"
            )
        else:
            context.log.error(
                f"Debug information for failed k8s job {job_name}:\n\n{pod_debug_info}"
            )

        if delete_failed_k8s_jobs:
            context.log.info(
                f"Deleting Kubernetes job {job_name} in namespace {namespace} due to exception"
            )
            api_client.delete_job(job_name=job_name, namespace=namespace)
        raise e


@op(ins={"start_after": In(Nothing)}, config_schema=K8S_JOB_OP_CONFIG)
@beta
def k8s_job_op(context):
    """An op that runs a Kubernetes job using the k8s API.

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

    You can create your own op with the same implementation by calling the `execute_k8s_job` function
    inside your own op.

    The service account that is used to run this job should have the following RBAC permissions:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/kubernetes/k8s_job_op_rbac.yaml
       :language: YAML
    """
    if "merge_behavior" in context.op_config:
        merge_behavior = K8sConfigMergeBehavior(context.op_config.pop("merge_behavior"))
    else:
        merge_behavior = K8sConfigMergeBehavior.DEEP

    execute_k8s_job(context, merge_behavior=merge_behavior, **context.op_config)
