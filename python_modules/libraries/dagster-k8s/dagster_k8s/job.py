import copy
import json
import random
import string
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, NamedTuple, Optional

import dagster._check as check
import kubernetes
from dagster import (
    Array,
    BoolSource,
    Enum as DagsterEnum,
    Field,
    Map,
    Noneable,
    StringSource,
)
from dagster._config import Permissive, Shape, validate_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.utils import parse_env_var
from dagster._serdes import whitelist_for_serdes
from dagster._utils.merger import merge_dicts
from dagster._utils.security import non_secure_md5_hash_str

from dagster_k8s.models import k8s_model_from_dict, k8s_snake_case_dict
from dagster_k8s.utils import get_common_labels, sanitize_k8s_label

# To retry step worker, users should raise RetryRequested() so that the dagster system is aware of the
# retry. As an example, see retry_job in dagster_test.test_project.test_jobs.repo
# To override this config, user can specify UserDefinedDagsterK8sConfig.
DEFAULT_K8S_JOB_BACKOFF_LIMIT = 0

DEFAULT_K8S_JOB_TTL_SECONDS_AFTER_FINISHED = 24 * 60 * 60  # 1 day

DAGSTER_HOME_DEFAULT = "/opt/dagster/dagster_home"

# The Kubernetes Secret containing the PG password will be exposed as this env var in the job
# container.
DAGSTER_PG_PASSWORD_ENV_VAR = "DAGSTER_PG_PASSWORD"

# We expect the PG secret to have this key.
#
# For an example, see:
# helm/dagster/templates/secret-postgres.yaml
DAGSTER_PG_PASSWORD_SECRET_KEY = "postgresql-password"

# Kubernetes Job object names cannot be longer than 63 characters
MAX_K8S_NAME_LEN = 63

# TODO: Deprecate this tag
K8S_RESOURCE_REQUIREMENTS_KEY = "dagster-k8s/resource_requirements"
K8S_RESOURCE_REQUIREMENTS_SCHEMA = Shape({"limits": Permissive(), "requests": Permissive()})


class K8sConfigMergeBehavior(Enum):
    SHALLOW = (  # Top-level keys in each of 'container_config' / 'pod_spec_config' are replaced
        "SHALLOW"
    )
    DEEP = (  # Dictionaries are deep-merged, lists are appended after removing values that are already present
        "DEEP"
    )


USER_DEFINED_K8S_CONFIG_KEY = "dagster-k8s/config"
USER_DEFINED_K8S_JOB_CONFIG_SCHEMA = Shape(
    {
        "container_config": Permissive(),
        "pod_template_spec_metadata": Permissive(),
        "pod_spec_config": Permissive(),
        "job_config": Permissive(),
        "job_metadata": Permissive(),
        "job_spec_config": Permissive(),
        "merge_behavior": Field(
            DagsterEnum.from_python_enum(K8sConfigMergeBehavior),
            is_required=False,
        ),
    }
)

DEFAULT_JOB_SPEC_CONFIG = {
    "ttl_seconds_after_finished": DEFAULT_K8S_JOB_TTL_SECONDS_AFTER_FINISHED,
    "backoff_limit": DEFAULT_K8S_JOB_BACKOFF_LIMIT,
}


class UserDefinedDagsterK8sConfig(
    NamedTuple(
        "_UserDefinedDagsterK8sConfig",
        [
            ("container_config", Mapping[str, Any]),
            ("pod_template_spec_metadata", Mapping[str, Any]),
            ("pod_spec_config", Mapping[str, Any]),
            ("job_config", Mapping[str, Any]),
            ("job_metadata", Mapping[str, Any]),
            ("job_spec_config", Mapping[str, Any]),
            ("deployment_metadata", Mapping[str, Any]),
            ("service_metadata", Mapping[str, Any]),
            ("merge_behavior", K8sConfigMergeBehavior),
        ],
    )
):
    def __new__(
        cls,
        *,
        container_config: Optional[Mapping[str, Any]] = None,
        pod_template_spec_metadata: Optional[Mapping[str, Any]] = None,
        pod_spec_config: Optional[Mapping[str, Any]] = None,
        job_config: Optional[Mapping[str, Any]] = None,
        job_metadata: Optional[Mapping[str, Any]] = None,
        job_spec_config: Optional[Mapping[str, Any]] = None,
        deployment_metadata: Optional[Mapping[str, Any]] = None,
        service_metadata: Optional[Mapping[str, Any]] = None,
        merge_behavior: K8sConfigMergeBehavior = K8sConfigMergeBehavior.DEEP,
    ):
        container_config = check.opt_mapping_param(
            container_config, "container_config", key_type=str
        )
        pod_template_spec_metadata = check.opt_mapping_param(
            pod_template_spec_metadata, "pod_template_spec_metadata", key_type=str
        )
        pod_spec_config = check.opt_mapping_param(pod_spec_config, "pod_spec_config", key_type=str)
        job_config = check.opt_mapping_param(job_config, "job_config", key_type=str)
        job_metadata = check.opt_mapping_param(job_metadata, "job_metadata", key_type=str)
        job_spec_config = check.opt_mapping_param(job_spec_config, "job_spec_config", key_type=str)

        deployment_metadata = check.opt_mapping_param(
            deployment_metadata, "deployment_metadata", key_type=str
        )
        service_metadata = check.opt_mapping_param(
            service_metadata, "service_metadata", key_type=str
        )

        if container_config:
            container_config = k8s_snake_case_dict(kubernetes.client.V1Container, container_config)

        if pod_template_spec_metadata:
            pod_template_spec_metadata = k8s_snake_case_dict(
                kubernetes.client.V1ObjectMeta, pod_template_spec_metadata
            )

        if pod_spec_config:
            pod_spec_config = k8s_snake_case_dict(kubernetes.client.V1PodSpec, pod_spec_config)

        if job_config:
            job_config = k8s_snake_case_dict(kubernetes.client.V1Job, job_config)

        if job_metadata:
            job_metadata = k8s_snake_case_dict(kubernetes.client.V1ObjectMeta, job_metadata)

        if job_spec_config:
            job_spec_config = k8s_snake_case_dict(kubernetes.client.V1JobSpec, job_spec_config)

        if deployment_metadata:
            deployment_metadata = k8s_snake_case_dict(
                kubernetes.client.V1ObjectMeta, deployment_metadata
            )

        if service_metadata:
            service_metadata = k8s_snake_case_dict(kubernetes.client.V1ObjectMeta, service_metadata)

        return super().__new__(
            cls,
            container_config=container_config,
            pod_template_spec_metadata=pod_template_spec_metadata,
            pod_spec_config=pod_spec_config,
            job_config=job_config,
            job_metadata=job_metadata,
            job_spec_config=job_spec_config,
            deployment_metadata=deployment_metadata,
            service_metadata=service_metadata,
            merge_behavior=check.inst_param(
                merge_behavior, "merge_behavior", K8sConfigMergeBehavior
            ),
        )

    def to_dict(self):
        return {
            "container_config": self.container_config,
            "pod_template_spec_metadata": self.pod_template_spec_metadata,
            "pod_spec_config": self.pod_spec_config,
            "job_config": self.job_config,
            "job_metadata": self.job_metadata,
            "job_spec_config": self.job_spec_config,
            "deployment_metadata": self.deployment_metadata,
            "service_metadata": self.service_metadata,
            "merge_behavior": self.merge_behavior.value,
        }

    @classmethod
    def from_dict(cls, config_dict):
        return UserDefinedDagsterK8sConfig(
            container_config=config_dict.get("container_config"),
            pod_template_spec_metadata=config_dict.get("pod_template_spec_metadata"),
            pod_spec_config=config_dict.get("pod_spec_config"),
            job_config=config_dict.get("job_config"),
            job_metadata=config_dict.get("job_metadata"),
            job_spec_config=config_dict.get("job_spec_config"),
            deployment_metadata=config_dict.get("deployment_metadata"),
            service_metadata=config_dict.get("service_metadata"),
            merge_behavior=K8sConfigMergeBehavior(
                config_dict.get("merge_behavior", K8sConfigMergeBehavior.DEEP.value)
            ),
        )


def get_k8s_resource_requirements(tags: Mapping[str, str]):
    check.mapping_param(tags, "tags", key_type=str, value_type=str)
    check.invariant(K8S_RESOURCE_REQUIREMENTS_KEY in tags)

    resource_requirements = json.loads(tags[K8S_RESOURCE_REQUIREMENTS_KEY])
    result = validate_config(K8S_RESOURCE_REQUIREMENTS_SCHEMA, resource_requirements)

    if not result.success:
        raise DagsterInvalidConfigError(
            f"Error in tags for {K8S_RESOURCE_REQUIREMENTS_KEY}",
            result.errors,
            result,
        )

    return result.value


def get_user_defined_k8s_config(tags: Mapping[str, str]):
    check.mapping_param(tags, "tags", key_type=str, value_type=str)

    if not any(key in tags for key in [K8S_RESOURCE_REQUIREMENTS_KEY, USER_DEFINED_K8S_CONFIG_KEY]):
        return UserDefinedDagsterK8sConfig()

    user_defined_k8s_config = {}

    if USER_DEFINED_K8S_CONFIG_KEY in tags:
        user_defined_k8s_config_value = json.loads(tags[USER_DEFINED_K8S_CONFIG_KEY])
        result = validate_config(USER_DEFINED_K8S_JOB_CONFIG_SCHEMA, user_defined_k8s_config_value)

        if not result.success:
            raise DagsterInvalidConfigError(
                f"Error in tags for {USER_DEFINED_K8S_CONFIG_KEY}",
                result.errors,
                result,
            )

        user_defined_k8s_config = check.not_none(result.value)

    container_config = user_defined_k8s_config.get("container_config", {})

    # Backcompat for resource requirements key
    if K8S_RESOURCE_REQUIREMENTS_KEY in tags:
        resource_requirements_config = get_k8s_resource_requirements(tags)
        container_config = merge_dicts(
            container_config, {"resources": resource_requirements_config}
        )

    return UserDefinedDagsterK8sConfig(
        container_config=container_config,
        pod_template_spec_metadata=user_defined_k8s_config.get("pod_template_spec_metadata"),
        pod_spec_config=user_defined_k8s_config.get("pod_spec_config"),
        job_config=user_defined_k8s_config.get("job_config"),
        job_metadata=user_defined_k8s_config.get("job_metadata"),
        job_spec_config=user_defined_k8s_config.get("job_spec_config"),
        deployment_metadata=user_defined_k8s_config.get("deployment_metadata"),
        service_metadata=user_defined_k8s_config.get("service_metadata"),
        merge_behavior=K8sConfigMergeBehavior(
            user_defined_k8s_config.get("merge_behavior", K8sConfigMergeBehavior.DEEP.value)
        ),
    )


def get_job_name_from_run_id(run_id, resume_attempt_number=None):
    return f"dagster-run-{run_id}" + (
        "" if not resume_attempt_number else f"-{resume_attempt_number}"
    )


@whitelist_for_serdes
class DagsterK8sJobConfig(
    NamedTuple(
        "_K8sJobTaskConfig",
        [
            ("job_image", Optional[str]),
            ("dagster_home", Optional[str]),
            ("image_pull_policy", str),
            ("image_pull_secrets", Sequence[Mapping[str, str]]),
            ("service_account_name", Optional[str]),
            ("instance_config_map", Optional[str]),
            ("postgres_password_secret", Optional[str]),
            ("env_config_maps", Sequence[str]),
            ("env_secrets", Sequence[str]),
            ("env_vars", Sequence[str]),
            ("volume_mounts", Sequence[Mapping[str, Any]]),
            ("volumes", Sequence[Mapping[str, Any]]),
            ("labels", Mapping[str, str]),
            ("resources", Mapping[str, Any]),
            ("scheduler_name", Optional[str]),
            ("security_context", Mapping[str, Any]),
        ],
    )
):
    """Configuration parameters for launching Dagster Jobs on Kubernetes.

    Params:
        dagster_home (str): The location of DAGSTER_HOME in the Job container; this is where the
            ``dagster.yaml`` file will be mounted from the instance ConfigMap specified here.
        image_pull_policy (Optional[str]): Allows the image pull policy to be overridden, e.g. to
            facilitate local testing with `kind <https://kind.sigs.k8s.io/>`_. Default:
            ``"Always"``. See:
            https://kubernetes.io/docs/concepts/containers/images/#updating-images.
        image_pull_secrets (Optional[Sequence[Mapping[str, str]]]): Optionally, a list of dicts, each of
            which corresponds to a Kubernetes ``LocalObjectReference`` (e.g.,
            ``{'name': 'myRegistryName'}``). This allows you to specify the ```imagePullSecrets`` on
            a pod basis. Typically, these will be provided through the service account, when needed,
            and you will not need to pass this argument. See:
            https://kubernetes.io/docs/concepts/containers/images/#specifying-imagepullsecrets-on-a-pod
            and https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.17/#podspec-v1-core
        service_account_name (Optional[str]): The name of the Kubernetes service account under which
            to run the Job. Defaults to "default"
        instance_config_map (str): The ``name`` of an existing Volume to mount into the pod in
            order to provide a ConfigMap for the Dagster instance. This Volume should contain a
            ``dagster.yaml`` with appropriate values for run storage, event log storage, etc.
        postgres_password_secret (Optional[str]): The name of the Kubernetes Secret where the postgres
            password can be retrieved. Will be mounted and supplied as an environment variable to
            the Job Pod.
        env_config_maps (Optional[Sequence[str]]): A list of custom ConfigMapEnvSource names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
            https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container
        env_secrets (Optional[Sequence[str]]): A list of custom Secret names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
            https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables
        env_vars (Optional[Sequence[str]]): A list of environment variables to inject into the Job.
            Default: ``[]``. See: https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables
        job_image (Optional[str]): The docker image to use. The Job container will be launched with this
            image. Should not be specified if using userDeployments.
        volume_mounts (Optional[Sequence[Permissive]]): A list of volume mounts to include in the job's
            container. Default: ``[]``. See:
            https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volumemount-v1-core
        volumes (Optional[List[Permissive]]): A list of volumes to include in the Job's Pod. Default: ``[]``. See:
            https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volume-v1-core
        labels (Optional[Mapping[str, str]]): Additional labels that should be included in the Job's Pod. See:
            https://kubernetes.io/docs/concepts/overview/working-with-objects/labels
        resources (Optional[Mapping[str, Any]]) Compute resource requirements for the container. See:
            https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
        scheduler_name (Optional[str]): Use a custom Kubernetes scheduler for launched Pods. See:
            https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/
        security_context (Optional[Mapping[str,Any]]): Security settings for the container. See:
            https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container
    """

    def __new__(
        cls,
        job_image: Optional[str] = None,
        dagster_home: Optional[str] = None,
        image_pull_policy: Optional[str] = None,
        image_pull_secrets: Optional[Sequence[Mapping[str, str]]] = None,
        service_account_name: Optional[str] = None,
        instance_config_map: Optional[str] = None,
        postgres_password_secret: Optional[str] = None,
        env_config_maps: Optional[Sequence[str]] = None,
        env_secrets: Optional[Sequence[str]] = None,
        env_vars: Optional[Sequence[str]] = None,
        volume_mounts: Optional[Sequence[Mapping[str, Any]]] = None,
        volumes: Optional[Sequence[Mapping[str, Any]]] = None,
        labels: Optional[Mapping[str, str]] = None,
        resources: Optional[Mapping[str, Any]] = None,
        scheduler_name: Optional[str] = None,
        security_context: Optional[Mapping[str, Any]] = None,
    ):
        return super().__new__(
            cls,
            job_image=check.opt_str_param(job_image, "job_image"),
            dagster_home=check.opt_str_param(dagster_home, "dagster_home"),
            image_pull_policy=check.opt_str_param(image_pull_policy, "image_pull_policy", "Always"),
            image_pull_secrets=check.opt_sequence_param(
                image_pull_secrets, "image_pull_secrets", of_type=Mapping
            ),
            service_account_name=check.opt_str_param(service_account_name, "service_account_name"),
            instance_config_map=check.opt_str_param(instance_config_map, "instance_config_map"),
            postgres_password_secret=check.opt_str_param(
                postgres_password_secret, "postgres_password_secret"
            ),
            env_config_maps=check.opt_sequence_param(
                env_config_maps, "env_config_maps", of_type=str
            ),
            env_secrets=check.opt_sequence_param(env_secrets, "env_secrets", of_type=str),
            env_vars=check.opt_sequence_param(env_vars, "env_vars", of_type=str),
            volume_mounts=[
                k8s_snake_case_dict(kubernetes.client.V1VolumeMount, mount)
                for mount in check.opt_sequence_param(volume_mounts, "volume_mounts")
            ],
            volumes=[
                k8s_snake_case_dict(kubernetes.client.V1Volume, volume)
                for volume in check.opt_sequence_param(volumes, "volumes")
            ],
            labels=check.opt_mapping_param(labels, "labels", key_type=str, value_type=str),
            resources=check.opt_mapping_param(resources, "resources", key_type=str),
            scheduler_name=check.opt_str_param(scheduler_name, "scheduler_name"),
            security_context=check.opt_mapping_param(security_context, "security_context"),
        )

    @classmethod
    def config_type_run_launcher(cls):
        """Configuration intended to be set on the Dagster instance for the run launcher."""
        return merge_dicts(
            DagsterK8sJobConfig.config_type_job(),
            {
                "instance_config_map": Field(
                    StringSource,
                    is_required=True,
                    description=(
                        "The ``name`` of an existing Volume to mount into the pod in order to"
                        " provide a ConfigMap for the Dagster instance. This Volume should contain"
                        " a ``dagster.yaml`` with appropriate values for run storage, event log"
                        " storage, etc."
                    ),
                ),
                "postgres_password_secret": Field(
                    StringSource,
                    is_required=False,
                    description=(
                        "The name of the Kubernetes Secret where the postgres password can be"
                        " retrieved. Will be mounted and supplied as an environment variable to the"
                        ' Job Pod.Secret must contain the key ``"postgresql-password"`` which will'
                        " be exposed in the Job environment as the environment variable"
                        " ``DAGSTER_PG_PASSWORD``."
                    ),
                ),
                "dagster_home": Field(
                    StringSource,
                    is_required=False,
                    default_value=DAGSTER_HOME_DEFAULT,
                    description=(
                        "The location of DAGSTER_HOME in the Job container; this is where the"
                        " ``dagster.yaml`` file will be mounted from the instance ConfigMap"
                        " specified here. Defaults to /opt/dagster/dagster_home."
                    ),
                ),
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
                        "The kubeconfig file from which to load config. Defaults to using the"
                        " default kubeconfig."
                    ),
                ),
                "fail_pod_on_run_failure": Field(
                    bool,
                    is_required=False,
                    description=(
                        "Whether the launched Kubernetes Jobs and Pods should fail if the Dagster"
                        " run fails"
                    ),
                ),
                "run_k8s_config": Field(
                    Shape(
                        {
                            "container_config": Permissive(),
                            "pod_template_spec_metadata": Permissive(),
                            "pod_spec_config": Permissive(),
                            "job_config": Permissive(),
                            "job_metadata": Permissive(),
                            "job_spec_config": Permissive(),
                        }
                    ),
                    is_required=False,
                    description="Raw Kubernetes configuration for launched runs.",
                ),
                "job_namespace": Field(StringSource, is_required=False, default_value="default"),
                "only_allow_user_defined_k8s_config_fields": Field(
                    Shape(
                        {
                            "container_config": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "pod_spec_config": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "pod_template_spec_metadata": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "job_metadata": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "job_spec_config": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "namespace": Field(BoolSource, is_required=False),
                        }
                    ),
                    is_required=False,
                    description="Dictionary of fields that are allowed to be configured on a "
                    "per-run or per-code-location basis - e.g. using tags on the run. "
                    "Can be used to prevent user code from being able to set arbitrary kubernetes "
                    "config on the pods launched by the run launcher.",
                ),
                "only_allow_user_defined_env_vars": Field(
                    Array(str),
                    is_required=False,
                    description="List of environment variable names that are allowed to be set on "
                    "a per-run or per-code-location basis - e.g. using tags on the run. ",
                ),
            },
        )

    @classmethod
    def config_type_job(cls):
        """Configuration intended to be set when creating a k8s job (e.g. in an executor that runs
        each op in its own k8s job, or a run launcher that create a k8s job for the run worker).
        Shares most of the schema with the container_context, but for back-compat reasons,
        'namespace' is called 'job_namespace'.
        """
        return merge_dicts(
            {
                "job_image": Field(
                    Noneable(StringSource),
                    is_required=False,
                    description=(
                        "Docker image to use for launched Jobs. If this field is empty, the image"
                        " that was used to originally load the Dagster repository will be used."
                        ' (Ex: "mycompany.com/dagster-k8s-image:latest").'
                    ),
                ),
            },
            DagsterK8sJobConfig.config_type_container(),
        )

    @classmethod
    def config_type_container(cls):
        return {
            "image_pull_policy": Field(
                Noneable(StringSource),
                is_required=False,
                description="Image pull policy to set on launched Pods.",
            ),
            "image_pull_secrets": Field(
                Noneable(Array(Shape({"name": StringSource}))),
                is_required=False,
                description=(
                    "Specifies that Kubernetes should get the credentials from "
                    "the Secrets named in this list."
                ),
            ),
            "service_account_name": Field(
                Noneable(StringSource),
                is_required=False,
                description="The name of the Kubernetes service account under which to run.",
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
            "env_vars": Field(
                Noneable(Array(str)),
                is_required=False,
                description=(
                    "A list of environment variables to inject into the Job. Each can be "
                    "of the form KEY=VALUE or just KEY (in which case the value will be pulled"
                    " from "
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
                    "A list of volume mounts to include in the job's container. Default: ``[]``."
                    " See: "
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

    @classmethod
    def config_type_container_context(cls):
        return merge_dicts(
            DagsterK8sJobConfig.config_type_container(),
            {
                "namespace": Field(
                    Noneable(StringSource),
                    is_required=False,
                    description=(
                        "The namespace into which to launch Kubernetes resources. Note that any "
                        "other required resources (such as the service account) must be "
                        "present in this namespace."
                    ),
                ),
                "run_k8s_config": Field(
                    USER_DEFINED_K8S_JOB_CONFIG_SCHEMA,
                    is_required=False,
                    description="Raw Kubernetes configuration for launched runs.",
                ),
                "server_k8s_config": Field(
                    Shape(
                        {
                            "container_config": Permissive(),
                            "pod_spec_config": Permissive(),
                            "pod_template_spec_metadata": Permissive(),
                            "merge_behavior": Field(
                                DagsterEnum.from_python_enum(K8sConfigMergeBehavior),
                                is_required=False,
                            ),
                            "deployment_metadata": Permissive(),
                            "service_metadata": Permissive(),
                        }
                    ),
                    is_required=False,
                    description="Raw Kubernetes configuration for launched code servers.",
                ),
                "env": Field(
                    Array(
                        Permissive(
                            {
                                "name": str,
                            }
                        )
                    ),
                    is_required=False,
                    default_value=[],
                ),
            },
        )

    @property
    def env(self) -> Sequence[Mapping[str, Optional[str]]]:
        parsed_env_vars = [parse_env_var(key) for key in (self.env_vars or [])]
        return [
            {"name": parsed_env_var[0], "value": parsed_env_var[1]}
            for parsed_env_var in parsed_env_vars
        ]

    @property
    def env_from_sources(self) -> Sequence[Mapping[str, Any]]:
        """This constructs a list of env_from sources. Along with a default base environment
        config map which we always load, the ConfigMaps and Secrets specified via
        env_config_maps and env_secrets will be pulled into the job construction here.
        """
        config_maps = [
            {"config_map_ref": {"name": config_map}} for config_map in self.env_config_maps
        ]

        secrets = [{"secret_ref": {"name": secret}} for secret in self.env_secrets]

        return config_maps + secrets

    def to_dict(self):
        return self._asdict()

    def with_image(self, image):
        return self._replace(job_image=image)

    @staticmethod
    def from_dict(config: Mapping[str, Any]):
        return DagsterK8sJobConfig(**config)


def construct_dagster_k8s_job(
    job_config: DagsterK8sJobConfig,
    args: Optional[Sequence[str]],
    job_name: str,
    user_defined_k8s_config: Optional[UserDefinedDagsterK8sConfig] = None,
    pod_name: Optional[str] = None,
    component: Optional[str] = None,
    labels: Optional[Mapping[str, str]] = None,
    env_vars: Optional[Sequence[Mapping[str, Any]]] = None,
) -> kubernetes.client.V1Job:
    """Constructs a Kubernetes Job object.

    Args:
        job_config: Job configuration to use for constructing the Kubernetes
            Job object.
        args: CLI arguments to use with in this Job.
        job_name: The name of the Job. Note that this name must be <= 63 characters in length.
        user_defined_k8s_config: Additional k8s config in tags or Dagster config
            to apply to the job.
        pod_name: The name of the Pod. Note that this name must be <= 63 characters
            in length. Defaults to "<job_name>-pod".
        component: The name of the component, used to provide the Job label
            app.kubernetes.io/component. Defaults to None.
        labels: Additional labels to be attached to k8s jobs and pod templates.
            Long label values are may be truncated.
        env_vars: Environment config for the container in the pod template.

    Returns:
        kubernetes.client.V1Job: A Kubernetes Job object.
    """
    check.inst_param(job_config, "job_config", DagsterK8sJobConfig)
    check.opt_sequence_param(args, "args", of_type=str)
    check.str_param(job_name, "job_name")
    user_defined_k8s_config = check.opt_inst_param(
        user_defined_k8s_config,
        "user_defined_k8s_config",
        UserDefinedDagsterK8sConfig,
        default=UserDefinedDagsterK8sConfig(),
    )

    pod_name = check.opt_str_param(pod_name, "pod_name", default=job_name + "-pod")
    check.opt_str_param(component, "component")
    check.opt_mapping_param(labels, "labels", key_type=str, value_type=str)

    check.invariant(
        len(job_name) <= MAX_K8S_NAME_LEN,
        "job_name is %d in length; Kubernetes Jobs cannot be longer than %d characters."  # noqa: UP031
        % (len(job_name), MAX_K8S_NAME_LEN),
    )

    check.invariant(
        len(pod_name) <= MAX_K8S_NAME_LEN,
        "job_name is %d in length; Kubernetes Pods cannot be longer than %d characters."  # noqa: UP031
        % (len(pod_name), MAX_K8S_NAME_LEN),
    )

    k8s_common_labels = get_common_labels()

    if component:
        k8s_common_labels["app.kubernetes.io/component"] = component

    additional_labels = {k: sanitize_k8s_label(v) for k, v in (labels or {}).items()}
    dagster_labels = merge_dicts(k8s_common_labels, additional_labels)

    env: list[Mapping[str, Any]] = []
    if env_vars:
        env.extend(env_vars)

    if job_config.dagster_home:
        env.append({"name": "DAGSTER_HOME", "value": job_config.dagster_home})

    if job_config.postgres_password_secret:
        env.append(
            {
                "name": DAGSTER_PG_PASSWORD_ENV_VAR,
                "value_from": {
                    "secret_key_ref": {
                        "name": job_config.postgres_password_secret,
                        "key": DAGSTER_PG_PASSWORD_SECRET_KEY,
                    }
                },
            }
        )

    container_config = copy.deepcopy(dict(user_defined_k8s_config.container_config))

    if args is not None:
        container_config["args"] = args

    user_defined_env_vars = container_config.pop("env", [])

    user_defined_env_from = container_config.pop("env_from", [])

    job_image = container_config.pop("image", job_config.job_image)

    image_pull_policy = container_config.pop("image_pull_policy", job_config.image_pull_policy)

    user_defined_k8s_volume_mounts = container_config.pop("volume_mounts", [])

    user_defined_resources = container_config.pop("resources", {})

    container_name = container_config.pop("name", "dagster")

    volume_mounts = [*job_config.volume_mounts, *user_defined_k8s_volume_mounts]

    resources = user_defined_resources if user_defined_resources else job_config.resources

    security_context = container_config.pop("security_context", job_config.security_context)

    container_config = merge_dicts(
        container_config,
        {
            "name": container_name,
            "image": job_image,
            "image_pull_policy": image_pull_policy,
            "env": [*env, *job_config.env, *user_defined_env_vars],
            "env_from": [*job_config.env_from_sources, *user_defined_env_from],
            "volume_mounts": volume_mounts,
            "resources": resources,
        },
        {"security_context": security_context} if security_context else {},
    )

    pod_spec_config = copy.deepcopy(dict(user_defined_k8s_config.pod_spec_config))

    user_defined_volumes = pod_spec_config.pop("volumes", [])

    volumes = [*job_config.volumes, *user_defined_volumes]

    # If the user has defined custom labels, remove them from the pod_template_spec_metadata
    # key and merge them with the dagster labels
    pod_template_spec_metadata = copy.deepcopy(
        dict(user_defined_k8s_config.pod_template_spec_metadata)
    )
    user_defined_pod_template_labels = pod_template_spec_metadata.pop("labels", {})

    service_account_name = pod_spec_config.pop(
        "service_account_name", job_config.service_account_name
    )

    scheduler_name = pod_spec_config.pop("scheduler_name", job_config.scheduler_name)

    automount_service_account_token = pod_spec_config.pop("automount_service_account_token", True)

    user_defined_containers = pod_spec_config.pop("containers", [])

    user_defined_image_pull_secrets = pod_spec_config.pop("image_pull_secrets", [])

    template = {
        "metadata": merge_dicts(
            pod_template_spec_metadata,
            {
                "name": pod_name,
                "labels": merge_dicts(
                    dagster_labels, job_config.labels, user_defined_pod_template_labels
                ),
            },
        ),
        "spec": merge_dicts(
            {"restart_policy": "Never"},
            pod_spec_config,
            {
                "image_pull_secrets": [
                    *job_config.image_pull_secrets,
                    *user_defined_image_pull_secrets,
                ],
                "service_account_name": service_account_name,
                "automount_service_account_token": automount_service_account_token,
                "containers": [container_config] + user_defined_containers,
                "volumes": volumes,
            },
            {"scheduler_name": scheduler_name} if scheduler_name else {},
        ),
    }

    job_spec_config = merge_dicts(
        DEFAULT_JOB_SPEC_CONFIG,
        user_defined_k8s_config.job_spec_config,
        {"template": template},
    )

    user_defined_job_metadata = copy.deepcopy(dict(user_defined_k8s_config.job_metadata))
    user_defined_job_labels = user_defined_job_metadata.pop("labels", {})

    job = k8s_model_from_dict(
        kubernetes.client.V1Job,
        merge_dicts(
            user_defined_k8s_config.job_config,
            {
                "api_version": "batch/v1",
                "kind": "Job",
                "metadata": merge_dicts(
                    user_defined_job_metadata,
                    {
                        "name": job_name,
                        "labels": merge_dicts(
                            dagster_labels, user_defined_job_labels, job_config.labels
                        ),
                    },
                ),
                "spec": job_spec_config,
            },
        ),
    )

    return job


def get_k8s_job_name(input_1, input_2=None):
    """Creates a unique (short!) identifier to name k8s objects based on run ID and step key(s).

    K8s Job names are limited to 63 characters, because they are used as labels. For more info, see:

    https://kubernetes.io/docs/concepts/overview/working-with-objects/names/
    """
    check.str_param(input_1, "input_1")
    check.opt_str_param(input_2, "input_2")
    if not input_2:
        letters = string.ascii_lowercase
        input_2 = "".join(random.choice(letters) for i in range(20))

    # Creates 32-bit signed int, so could be negative
    name_hash = non_secure_md5_hash_str((input_1 + input_2).encode("utf-8"))

    return name_hash
