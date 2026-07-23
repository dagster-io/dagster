import asyncio
import copy
import hashlib
import re
import time
from collections.abc import Mapping

import kubernetes
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.models import k8s_model_from_dict
from kubernetes import client

from dagster_cloud.instance import DagsterCloudAgentInstance
from dagster_cloud.workspace.user_code_launcher.utils import (
    deterministic_label_for_location,
    get_code_server_port,
    get_grpc_server_env,
    get_human_readable_label,
    unique_resource_name,
)

MANAGED_RESOURCES_LABEL = {"managed_by": "K8sUserCodeLauncher"}

# defs_state_info override ConfigMap — see in-place pin reload design.
DEFS_STATE_CONFIG_MAP_NAME_PREFIX = "dagster-defs-state-"
DEFS_STATE_OVERRIDE_FILENAME = "defs_state_info"
DEFS_STATE_MOUNT_PATH = "/var/run/dagster/defs-state"
DEFS_STATE_OVERRIDE_ENV = "DAGSTER_DEFS_STATE_INFO_OVERRIDE_PATH"
# Verbose to minimize collision with user-supplied volumes.
DEFS_STATE_VOLUME_NAME = "dagster-cloud-defs-state-override"

# Server spec version: bump when a new launcher mechanism (e.g. ConfigMap mount +
# DAGSTER_DEFS_STATE_INFO_OVERRIDE_PATH env var) makes a platform-induced pod
# restart safe under in-place defs_state_info reload. The capability gate keys
# off the running Deployment's label so legacy Deployments stay on
# destroy-and-recreate.
SERVER_SPEC_VERSION_LABEL_KEY = "dagster.io/server-spec-version"
SERVER_SPEC_VERSION_V2 = "v2"


def defs_state_config_map_name(k8s_deployment_name: str) -> str:
    """Per-incarnation ConfigMap name, keyed on the k8s Deployment resource name.

    Keyed per *incarnation* (the uuid-suffixed k8s Deployment name), NOT per
    location: during an update, old and new Deployments for the same location
    coexist, and removing the old server must never delete the ConfigMap the
    live replacement mounts. Each incarnation owns exactly one CM, created
    alongside it and deleted with it (``_remove_server_handle`` derives this
    name from ``handle.name``; strays are covered by the orphan GC sweep).

    Deterministic from the Deployment name so spinup, in-place reload, and
    cleanup all agree without listing. Hashed because prefix(19) + Deployment
    name(up to 63) would exceed the 63-char K8s resource-name limit:
    prefix(19) + sha1 hex(40) = 59 chars.
    """
    m = hashlib.sha1()
    m.update(k8s_deployment_name.encode())
    return f"{DEFS_STATE_CONFIG_MAP_NAME_PREFIX}{m.hexdigest()}"


def _get_dagster_k8s_labels(
    deployment_name: str,
    location_name: str,
    instance: DagsterCloudAgentInstance,
    server_timestamp: float,
) -> Mapping[str, str]:
    return {
        **MANAGED_RESOURCES_LABEL,
        "location_hash": deterministic_label_for_location(deployment_name, location_name),
        "location_name": get_k8s_human_readable_label(location_name),
        "deployment_name": get_k8s_human_readable_label(deployment_name),
        "agent_id": instance.instance_uuid,
        "server_timestamp": str(server_timestamp),
    }


def _sanitize_k8s_resource_name(name):
    filtered_name = re.sub("[^a-z0-9-]", "", name.lower())

    # ensure it doesn't start with a non-alpha character
    while filtered_name and re.match("[^a-z].*", filtered_name):
        filtered_name = filtered_name[1:]

    filtered_name = filtered_name.strip("-")

    # always return something that starts with a letter in the unlikely event that everything is
    # filtered out (doesn't have to be unique)
    return filtered_name or "k8s"


def unique_k8s_resource_name(deployment_name, location_name):
    """https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#dns-label-names.

    K8s resource names are restricted, so we must sanitize the location name to not include disallowed characters.
    """
    return unique_resource_name(
        deployment_name, location_name, length_limit=63, sanitize_fn=_sanitize_k8s_resource_name
    )


def get_k8s_human_readable_label(name):
    """https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set.

    K8s label values are restricted, so we must sanitize the location name to not include disallowed characters.
    These are purely to help humans debug, so they don't need to be unique.
    """
    return get_human_readable_label(
        name,
        length_limit=63,
        sanitize_fn=lambda name: (
            re.sub("[^a-zA-Z0-9-_.]", "", name).strip("-").strip("_").strip(".")
        ),
    )


def construct_defs_state_config_map(
    deployment_name: str,
    location_name: str,
    k8s_deployment_name: str,
    instance: DagsterCloudAgentInstance,
    server_timestamp: float,
    serialized_defs_state_info: str,
) -> client.V1ConfigMap:
    """ConfigMap holding the current serialized DefsStateInfo for a code-server.

    Mounted into the pod and read at boot via DAGSTER_DEFS_STATE_INFO_OVERRIDE_PATH.
    An empty string means "explicitly no pin" — the OSS-side reader treats a
    present-but-empty file as authoritative and does NOT fall back to the
    --defs-state-info arg, which may carry a stale pin from Deployment-creation
    time. Only a missing/unreadable file falls back to the arg. Labels mirror
    Deployment/Service so cleanup can use the same selectors.
    """
    return k8s_model_from_dict(
        client.V1ConfigMap,
        {
            "api_version": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": defs_state_config_map_name(k8s_deployment_name),
                "labels": _get_dagster_k8s_labels(
                    deployment_name, location_name, instance, server_timestamp
                ),
            },
            "data": {DEFS_STATE_OVERRIDE_FILENAME: serialized_defs_state_info},
        },
    )


def construct_code_location_service(
    deployment_name,
    location_name,
    service_name,
    container_context,
    instance,
    server_timestamp: float,
):
    user_defined_k8s_config = container_context.server_k8s_config
    user_defined_service_metadata = copy.deepcopy(dict(user_defined_k8s_config.service_metadata))
    user_defined_service_labels = user_defined_service_metadata.pop("labels", {})
    user_defined_service_spec_config = copy.deepcopy(
        dict(user_defined_k8s_config.service_spec_config)
    )

    return k8s_model_from_dict(
        client.V1Service,
        {
            "api_version": "v1",
            "kind": "Service",
            "metadata": {
                **user_defined_service_metadata,
                "name": service_name,
                "labels": {
                    **user_defined_service_labels,
                    **_get_dagster_k8s_labels(
                        deployment_name, location_name, instance, server_timestamp
                    ),
                },
            },
            "spec": {
                **user_defined_service_spec_config,
                "selector": {"user-deployment": service_name},
                "ports": [{"name": "grpc", "protocol": "TCP", "port": get_code_server_port()}],
            },
        },
    )


def construct_code_location_deployment(
    instance,
    *,
    deployment_name,
    location_name,
    k8s_deployment_name,
    metadata,
    container_context,
    args,
    server_timestamp: float,
    server_replica_count: int | None = None,
    mount_defs_state_config_map: bool = False,
):
    env = get_grpc_server_env(
        metadata,
        get_code_server_port(),
        location_name,
        instance.ref_for_deployment(deployment_name),
    )

    user_defined_config = container_context.server_k8s_config

    user_defined_deployment_metadata = copy.deepcopy(dict(user_defined_config.deployment_metadata))
    user_defined_deployment_labels = user_defined_deployment_metadata.pop("labels", {})

    container_config = copy.deepcopy(user_defined_config.container_config)

    user_defined_env_vars = container_config.pop("env", [])
    container_name = container_config.pop("name", "dagster")

    container_config = {
        **container_config,
        "args": args,
        "name": container_name,
        "image": metadata.image,
        "env": (
            [{"name": key, "value": value} for key, value in env.items()] + user_defined_env_vars
        ),
    }

    if mount_defs_state_config_map:
        # INVARIANT: must NOT use subPath. ConfigMap live-updates only propagate
        # to non-subPath mounts; the request path doesn't depend on the file
        # (gRPC handles in-flight updates) but the new-pod-restart path does.
        existing_mounts = container_config.setdefault("volume_mounts", [])
        for mount in existing_mounts:
            if mount.get("name") == DEFS_STATE_VOLUME_NAME:
                raise Exception(
                    f"User-supplied volume_mount '{DEFS_STATE_VOLUME_NAME}' collides with "
                    f"the reserved defs-state override mount. Rename your volume."
                )
        existing_mounts.append(
            {
                "name": DEFS_STATE_VOLUME_NAME,
                "mount_path": DEFS_STATE_MOUNT_PATH,
                "read_only": True,
            }
        )
        # Env var, NOT CLI arg. Old `dagster` versions silently ignore an unknown
        # env var; an unknown CLI flag would crash the pod on boot. This keeps
        # the rollout safe even if a customer's user-code image lags the agent.
        container_config["env"].append(
            {
                "name": DEFS_STATE_OVERRIDE_ENV,
                "value": f"{DEFS_STATE_MOUNT_PATH}/{DEFS_STATE_OVERRIDE_FILENAME}",
            }
        )

    # With multiple replicas the Service must only route traffic to pods whose gRPC
    # port is open. The Dagster gRPC server only binds its port after user code has
    # been imported (DagsterGrpcServer.serve -> server.start), so a tcpSocket probe
    # on that port is sufficient and matches the readiness signal the agent's own
    # client.ping uses. If the user already configured a probe, leave it alone.
    if (
        server_replica_count is not None
        and server_replica_count > 1
        and "readiness_probe" not in container_config
    ):
        container_config["readiness_probe"] = {
            "tcp_socket": {"port": get_code_server_port()},
        }

    pod_spec_config = copy.deepcopy(user_defined_config.pod_spec_config)

    user_defined_containers = pod_spec_config.pop("containers", [])

    pod_spec_config = {
        **pod_spec_config,
        "containers": [container_config] + user_defined_containers,
    }

    if mount_defs_state_config_map:
        # optional=True so a manually-deleted ConfigMap doesn't block pod startup
        # with CreateContainerConfigError; the pod falls through to args.
        existing_volumes = pod_spec_config.setdefault("volumes", [])
        for volume in existing_volumes:
            if volume.get("name") == DEFS_STATE_VOLUME_NAME:
                raise Exception(
                    f"User-supplied volume '{DEFS_STATE_VOLUME_NAME}' collides with the "
                    f"reserved defs-state override volume. Rename your volume."
                )
        existing_volumes.append(
            {
                "name": DEFS_STATE_VOLUME_NAME,
                "config_map": {
                    "name": defs_state_config_map_name(k8s_deployment_name),
                    "optional": True,
                },
            }
        )

    pod_template_spec_metadata = copy.deepcopy(user_defined_config.pod_template_spec_metadata)
    user_defined_pod_template_labels = pod_template_spec_metadata.pop("labels", {})

    dagster_labels = dict(
        _get_dagster_k8s_labels(deployment_name, location_name, instance, server_timestamp)
    )
    if mount_defs_state_config_map:
        # Capability gate keys off this label on the running Deployment so a
        # pre-mount Deployment never gets fast-path reload.
        dagster_labels[SERVER_SPEC_VERSION_LABEL_KEY] = SERVER_SPEC_VERSION_V2

    deployment_dict = {
        "metadata": {
            **user_defined_deployment_metadata,
            "name": k8s_deployment_name,
            "labels": {
                **user_defined_deployment_labels,
                **dagster_labels,
            },
        },
        "spec": {  # DeploymentSpec
            "selector": {"match_labels": {"user-deployment": k8s_deployment_name}},
            **({"replicas": server_replica_count} if server_replica_count is not None else {}),
            "template": {  # PodTemplateSpec
                "metadata": {
                    **pod_template_spec_metadata,
                    "labels": {
                        **user_defined_pod_template_labels,
                        **dagster_labels,
                        "user-deployment": k8s_deployment_name,
                    },
                },
                "spec": pod_spec_config,
            },
        },
    }

    return k8s_model_from_dict(
        kubernetes.client.V1Deployment,
        deployment_dict,
    )


def get_container_waiting_reason(pod) -> str | None:
    if (not pod.status.container_statuses) or len(pod.status.container_statuses) == 0:
        return None

    container_waiting_state = pod.status.container_statuses[0].state.waiting
    if not container_waiting_state:
        return None

    return container_waiting_state.reason


def get_deployment_failure_debug_info(
    k8s_deployment_name,
    namespace,
    core_api_client,
    pod_list,
    logger,
    apps_api_client,
):
    replicaset_debug_info = ""
    try:
        replicaset_list = apps_api_client.list_namespaced_replica_set(
            namespace, label_selector=f"user-deployment={k8s_deployment_name}"
        ).items
        if replicaset_list:
            replicaset = replicaset_list[0]
            replicaset_name = replicaset.metadata.name
            # Get warning events for the ReplicaSet
            warning_events = core_api_client.list_namespaced_event(
                namespace, field_selector=f"involvedObject.name={replicaset_name},type=Warning"
            ).items
            if not warning_events:
                replicaset_debug_info = f"No warning events for replicaset {replicaset_name}."
            else:
                event_strs = []
                for event in warning_events:
                    count_str = f" (x{event.count})" if (event.count and event.count > 1) else ""
                    event_strs.append(f"{event.reason}: {event.message}{count_str}")
                replicaset_debug_info = (
                    f"Warning events for replicaset {replicaset_name}:\n" + "\n".join(event_strs)
                )
    except:
        logger.exception("Failure fetching replicaset debug info")

    if not pod_list:
        pod_debug_info = ""
        kubectl_prompt = (
            "For more information about the failure, run `kubectl describe deployment"
            f" {k8s_deployment_name}` in your cluster."
        )
    else:
        pod = pod_list[0]
        pod_name = pod.metadata.name

        kubectl_prompt = (
            f"For more information about the failure, run `kubectl describe pod {pod_name}`"
            f" or `kubectl describe deployment {k8s_deployment_name}` in your cluster."
        )
        pod_debug_info = ""
        try:
            api_client = DagsterKubernetesClient.production_client(
                core_api_override=core_api_client
            )
            pod_debug_info = api_client.get_pod_debug_info(pod_name, namespace)
        except Exception:
            logger.exception(f"Error trying to get debug information for failed k8s pod {pod_name}")

    results = []
    if pod_debug_info:
        results.append(pod_debug_info)
    if replicaset_debug_info:
        results.append(replicaset_debug_info)
    if kubectl_prompt:
        results.append(kubectl_prompt)

    return "\n\n".join(results)


async def wait_for_deployment_complete(
    k8s_deployment_name,
    namespace,
    logger,
    location_name,
    metadata,
    timeout,
    image_pull_grace_period,
    core_api,
):
    """Translated from
    https://github.com/kubernetes/kubectl/blob/ac49920c0ccb0dd0899d5300fc43713ee2dfcdc9/pkg/polymorphichelpers/rollout_status.go#L75-L91.
    """
    api = client.AppsV1Api(client.ApiClient())

    start = time.time()

    pod_list = []

    while True:
        await asyncio.sleep(2)

        time_elapsed = time.time() - start

        if time_elapsed >= timeout:
            timeout_message: str = f"Timed out waiting for deployment {k8s_deployment_name}."
            debug_info = get_deployment_failure_debug_info(
                k8s_deployment_name, namespace, core_api, pod_list, logger, apps_api_client=api
            )
            if debug_info:
                timeout_message = timeout_message + "\n\n" + debug_info

            raise Exception(timeout_message)

        deployment = api.read_namespaced_deployment(k8s_deployment_name, namespace)
        status = deployment.status
        spec = deployment.spec

        logger.debug(
            f"[updated_replicas:{status.updated_replicas},replicas:{status.replicas},available_replicas:{status.available_replicas},observed_generation:{status.observed_generation}]"
            " waiting..."
        )
        logger.debug(f"Status: {status}, spec: {spec}")

        if (
            status.updated_replicas == spec.replicas  # new replicas have been updated
            and status.replicas == status.updated_replicas  # no old replicas pending termination
            and status.available_replicas == status.updated_replicas  # updated replicas available
            and status.observed_generation >= deployment.metadata.generation  # new spec observed
        ):
            return True

        pod_list = core_api.list_namespaced_pod(
            namespace, label_selector=f"user-deployment={k8s_deployment_name}"
        ).items

        if time_elapsed >= image_pull_grace_period:
            for pod in pod_list:
                waiting_reason = get_container_waiting_reason(pod)
                if (
                    waiting_reason == "ImagePullBackOff"
                    or waiting_reason == "ErrImageNeverPull"
                    or waiting_reason == "CreateContainerConfigError"
                ):
                    error_message = f"Error creating deployment for {k8s_deployment_name}."
                    debug_info = get_deployment_failure_debug_info(
                        k8s_deployment_name,
                        namespace,
                        core_api,
                        pod_list,
                        logger,
                        apps_api_client=api,
                    )
                    if debug_info:
                        error_message = error_message + "\n" + debug_info

                    raise Exception(error_message)
