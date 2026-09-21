from dagster import Array, BoolSource, Field, IntSource, Noneable, Permissive, Shape, StringSource

SHARED_K8S_CONFIG = {
    "server_replica_count": Field(
        IntSource,
        is_required=False,
        description=(
            "The number of code server replicas to launch for this code location. "
            "Defaults to 1. When set above 1, the agent will launch the same number "
            "of pods behind the code location's Service and load-balance gRPC requests "
            "across them. A readiness probe on the gRPC port is required so that "
            "Kubernetes only routes traffic to replicas whose user code has finished "
            "importing; a default tcpSocket probe is injected if none is configured."
        ),
    ),
    "namespace": Field(
        Noneable(StringSource),
        is_required=False,
        description=(
            "The namespace into which to launch Kubernetes resources. Note that any "
            "other required resources (such as the service account) must be "
            "present in this namespace."
        ),
    ),
    "image_pull_policy": Field(
        Noneable(StringSource),
        is_required=False,
        description="Image pull policy to set on launched Pods.",
    ),
    "env_config_maps": Field(
        Noneable(Array(StringSource)),
        is_required=False,
        description=(
            "A list of custom ConfigMapEnvSource names from which to draw "
            "environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:"
            "https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container"
        ),
    ),
    "env_secrets": Field(
        Noneable(Array(StringSource)),
        is_required=False,
        description=(
            "A list of custom Secret names from which to draw environment "
            "variables (using ``envFrom``) for the Job. Default: ``[]``. See:"
            "https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables"
        ),
    ),
    "service_account_name": Field(
        Noneable(StringSource),
        is_required=False,
        description="The name of the Kubernetes service account under which to run.",
    ),
    "env_vars": Field(
        Noneable(Array(str)),
        is_required=False,
        description=(
            "A list of environment variables to inject into the Job. Each can be "
            "of the form KEY=VALUE or just KEY (in which case the value will be pulled from "
            "the current process). Default: ``[]``. See: "
            "https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables"
        ),
    ),
    "volume_mounts": Field(
        Array(
            # Can supply either snake_case or camelCase, but in typeaheads based on the
            # schema we assume snake_case
            Permissive(
                {
                    "name": StringSource,
                    "mount_path": Field(StringSource, is_required=False),
                    "mount_propagation": Field(StringSource, is_required=False),
                    "read_only": Field(BoolSource, is_required=False),
                    "sub_path": Field(StringSource, is_required=False),
                    "sub_path_expr": Field(StringSource, is_required=False),
                }
            )
        ),
        is_required=False,
        default_value=[],
        description=(
            "A list of volume mounts to include in the job's container. Default: ``[]``. See: "
            "https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volumemount-v1-core"
        ),
    ),
    "volumes": Field(
        Array(
            Permissive(
                {
                    "name": str,
                }
            )
        ),
        is_required=False,
        default_value=[],
        description=(
            "A list of volumes to include in the Job's Pod. Default: ``[]``. For the many "
            "possible volume source types that can be included, see: "
            "https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volume-v1-core"
        ),
    ),
    "image_pull_secrets": Field(
        Noneable(Array(Shape({"name": StringSource}))),
        is_required=False,
        description=(
            "Specifies that Kubernetes should get the credentials from "
            "the Secrets named in this list."
        ),
    ),
    "labels": Field(
        dict,
        is_required=False,
        description=(
            "Labels to apply to all created pods. See: "
            "https://kubernetes.io/docs/concepts/overview/working-with-objects/labels"
        ),
    ),
    "resources": Field(
        Noneable(
            {
                "limits": Field(dict, is_required=False),
                "requests": Field(dict, is_required=False),
            }
        ),
        is_required=False,
        description=(
            "Compute resource requirements for the container. See: "
            "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"
        ),
    ),
    "scheduler_name": Field(
        Noneable(StringSource),
        is_required=False,
        description=(
            "Use a custom Kubernetes scheduler for launched Pods. See:"
            "https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/"
        ),
    ),
    "security_context": Field(
        dict,
        is_required=False,
        description=(
            "Security settings for the container. See:"
            "https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container"
        ),
    ),
}
