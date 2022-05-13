import copy
import hashlib
import json
import os
import random
import string
from collections import namedtuple
from typing import Any, Dict, List, Optional

import kubernetes

import dagster._check as check
from dagster import Array, BoolSource, Field, Noneable, StringSource
from dagster import __version__ as dagster_version
from dagster.config.field_utils import Permissive, Shape
from dagster.config.validate import validate_config
from dagster.core.errors import DagsterInvalidConfigError
from dagster.serdes import whitelist_for_serdes
from dagster.utils import frozentags, merge_dicts

from .models import k8s_model_from_dict, k8s_snake_case_dict
from .utils import sanitize_k8s_label

# To retry step worker, users should raise RetryRequested() so that the dagster system is aware of the
# retry. As an example, see retry_pipeline in dagster_test.test_project.test_pipelines.repo
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

USER_DEFINED_K8S_CONFIG_KEY = "dagster-k8s/config"
USER_DEFINED_K8S_CONFIG_SCHEMA = Shape(
    {
        "container_config": Permissive(),
        "pod_template_spec_metadata": Permissive(),
        "pod_spec_config": Permissive(),
        "job_config": Permissive(),
        "job_metadata": Permissive(),
        "job_spec_config": Permissive(),
    }
)

DEFAULT_JOB_SPEC_CONFIG = {
    "ttl_seconds_after_finished": DEFAULT_K8S_JOB_TTL_SECONDS_AFTER_FINISHED,
    "backoff_limit": DEFAULT_K8S_JOB_BACKOFF_LIMIT,
}


class UserDefinedDagsterK8sConfig(
    namedtuple(
        "_UserDefinedDagsterK8sConfig",
        "container_config pod_template_spec_metadata pod_spec_config job_config job_metadata job_spec_config",
    )
):
    def __new__(
        cls,
        container_config=None,
        pod_template_spec_metadata=None,
        pod_spec_config=None,
        job_config=None,
        job_metadata=None,
        job_spec_config=None,
    ):

        container_config = check.opt_dict_param(container_config, "container_config", key_type=str)
        pod_template_spec_metadata = check.opt_dict_param(
            pod_template_spec_metadata, "pod_template_spec_metadata", key_type=str
        )
        pod_spec_config = check.opt_dict_param(pod_spec_config, "pod_spec_config", key_type=str)
        job_config = check.opt_dict_param(job_config, "job_config", key_type=str)
        job_metadata = check.opt_dict_param(job_metadata, "job_metadata", key_type=str)
        job_spec_config = check.opt_dict_param(job_spec_config, "job_spec_config", key_type=str)

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

        return super(UserDefinedDagsterK8sConfig, cls).__new__(
            cls,
            container_config=container_config,
            pod_template_spec_metadata=pod_template_spec_metadata,
            pod_spec_config=pod_spec_config,
            job_config=job_config,
            job_metadata=job_metadata,
            job_spec_config=job_spec_config,
        )

    def to_dict(self):
        return {
            "container_config": self.container_config,
            "pod_template_spec_metadata": self.pod_template_spec_metadata,
            "pod_spec_config": self.pod_spec_config,
            "job_config": self.job_config,
            "job_metadata": self.job_metadata,
            "job_spec_config": self.job_spec_config,
        }

    @classmethod
    def from_dict(self, config_dict):
        return UserDefinedDagsterK8sConfig(
            container_config=config_dict.get("container_config"),
            pod_template_spec_metadata=config_dict.get("pod_template_spec_metadata"),
            pod_spec_config=config_dict.get("pod_spec_config"),
            job_config=config_dict.get("job_config"),
            job_metadata=config_dict.get("job_metadata"),
            job_spec_config=config_dict.get("job_spec_config"),
        )


def get_k8s_resource_requirements(tags):
    check.inst_param(tags, "tags", frozentags)
    check.invariant(K8S_RESOURCE_REQUIREMENTS_KEY in tags)

    resource_requirements = json.loads(tags[K8S_RESOURCE_REQUIREMENTS_KEY])
    result = validate_config(K8S_RESOURCE_REQUIREMENTS_SCHEMA, resource_requirements)

    if not result.success:
        raise DagsterInvalidConfigError(
            "Error in tags for {}".format(K8S_RESOURCE_REQUIREMENTS_KEY),
            result.errors,
            result,
        )

    return result.value


def get_user_defined_k8s_config(tags):
    check.inst_param(tags, "tags", frozentags)

    if not any(key in tags for key in [K8S_RESOURCE_REQUIREMENTS_KEY, USER_DEFINED_K8S_CONFIG_KEY]):
        return UserDefinedDagsterK8sConfig()

    user_defined_k8s_config = {}

    if USER_DEFINED_K8S_CONFIG_KEY in tags:
        user_defined_k8s_config_value = json.loads(tags[USER_DEFINED_K8S_CONFIG_KEY])
        result = validate_config(USER_DEFINED_K8S_CONFIG_SCHEMA, user_defined_k8s_config_value)

        if not result.success:
            raise DagsterInvalidConfigError(
                "Error in tags for {}".format(USER_DEFINED_K8S_CONFIG_KEY),
                result.errors,
                result,
            )

        user_defined_k8s_config = result.value

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
    )


def get_job_name_from_run_id(run_id, resume_attempt_number=None):
    return "dagster-run-{}".format(run_id) + (
        "" if not resume_attempt_number else "-{}".format(resume_attempt_number)
    )


@whitelist_for_serdes
class DagsterK8sJobConfig(
    namedtuple(
        "_K8sJobTaskConfig",
        "job_image dagster_home image_pull_policy image_pull_secrets service_account_name "
        "instance_config_map postgres_password_secret env_config_maps env_secrets env_vars "
        "volume_mounts volumes labels resources",
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
        image_pull_secrets (Optional[List[Dict[str, str]]]): Optionally, a list of dicts, each of
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
        env_config_maps (Optional[List[str]]): A list of custom ConfigMapEnvSource names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
            https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container
        env_secrets (Optional[List[str]]): A list of custom Secret names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
            https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables
        env_vars (Optional[List[str]]): A list of environment variables to inject into the Job.
            Default: ``[]``. See: https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables
        job_image (Optional[str]): The docker image to use. The Job container will be launched with this
            image. Should not be specified if using userDeployments.
        volume_mounts (Optional[List[Permissive]]): A list of volume mounts to include in the job's
            container. Default: ``[]``. See:
            https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volumemount-v1-core
        volumes (Optional[List[Permissive]]): A list of volumes to include in the Job's Pod. Default: ``[]``. See:
            https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volume-v1-core
        labels (Optional[Dict[str, str]]): Additional labels that should be included in the Job's Pod. See:
            https://kubernetes.io/docs/concepts/overview/working-with-objects/labels
        resources (Optional[Dict[str, Any]]) Compute resource requirements for the container. See:
            https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
    """

    def __new__(
        cls,
        job_image=None,
        dagster_home=None,
        image_pull_policy=None,
        image_pull_secrets=None,
        service_account_name=None,
        instance_config_map=None,
        postgres_password_secret=None,
        env_config_maps=None,
        env_secrets=None,
        env_vars=None,
        volume_mounts=None,
        volumes=None,
        labels=None,
        resources=None,
    ):
        return super(DagsterK8sJobConfig, cls).__new__(
            cls,
            job_image=check.opt_str_param(job_image, "job_image"),
            dagster_home=check.opt_str_param(
                dagster_home, "dagster_home", default=DAGSTER_HOME_DEFAULT
            ),
            image_pull_policy=check.opt_str_param(image_pull_policy, "image_pull_policy", "Always"),
            image_pull_secrets=check.opt_list_param(
                image_pull_secrets, "image_pull_secrets", of_type=dict
            ),
            service_account_name=check.opt_str_param(service_account_name, "service_account_name"),
            instance_config_map=check.str_param(instance_config_map, "instance_config_map"),
            postgres_password_secret=check.opt_str_param(
                postgres_password_secret, "postgres_password_secret"
            ),
            env_config_maps=check.opt_list_param(env_config_maps, "env_config_maps", of_type=str),
            env_secrets=check.opt_list_param(env_secrets, "env_secrets", of_type=str),
            env_vars=check.opt_list_param(env_vars, "env_vars", of_type=str),
            volume_mounts=[
                k8s_snake_case_dict(kubernetes.client.V1VolumeMount, mount)
                for mount in check.opt_list_param(volume_mounts, "volume_mounts")
            ],
            volumes=[
                k8s_snake_case_dict(kubernetes.client.V1Volume, volume)
                for volume in check.opt_list_param(volumes, "volumes")
            ],
            labels=check.opt_dict_param(labels, "labels", key_type=str, value_type=str),
            resources=check.opt_dict_param(resources, "resources", key_type=str),
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
                    description="The ``name`` of an existing Volume to mount into the pod in order to "
                    "provide a ConfigMap for the Dagster instance. This Volume should contain a "
                    "``dagster.yaml`` with appropriate values for run storage, event log storage, etc.",
                ),
                "postgres_password_secret": Field(
                    StringSource,
                    is_required=False,
                    description="The name of the Kubernetes Secret where the postgres password can be "
                    "retrieved. Will be mounted and supplied as an environment variable to the Job Pod."
                    'Secret must contain the key ``"postgresql-password"`` which will be exposed in '
                    "the Job environment as the environment variable ``DAGSTER_PG_PASSWORD``.",
                ),
                "dagster_home": Field(
                    StringSource,
                    is_required=False,
                    default_value=DAGSTER_HOME_DEFAULT,
                    description="The location of DAGSTER_HOME in the Job container; this is where the "
                    "``dagster.yaml`` file will be mounted from the instance ConfigMap specified here. "
                    "Defaults to /opt/dagster/dagster_home.",
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
                    description="The kubeconfig file from which to load config. Defaults to using the default kubeconfig.",
                ),
                "fail_pod_on_run_failure": Field(
                    bool,
                    is_required=False,
                    description="Whether the launched Kubernetes Jobs and Pods should fail if the Dagster run fails",
                ),
            },
        )

    @classmethod
    def config_type_job(cls):
        """Configuration intended to be set when creating a k8s job (e.g. in an executor that runs
        each op in its own k8s job, or a run launcher that create a k8s job for the run worker).
        Shares most of the schema with the container_context, but for back-compat reasons,
        'namespace' is called 'job_namespace'."""

        return merge_dicts(
            {
                "job_image": Field(
                    Noneable(StringSource),
                    is_required=False,
                    description="Docker image to use for launched Jobs. If this field is empty, "
                    "the image that was used to originally load the Dagster repository will be used. "
                    '(Ex: "mycompany.com/dagster-k8s-image:latest").',
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
                description="Specifies that Kubernetes should get the credentials from "
                "the Secrets named in this list.",
            ),
            "service_account_name": Field(
                Noneable(StringSource),
                is_required=False,
                description="The name of the Kubernetes service account under which to run.",
            ),
            "env_config_maps": Field(
                Noneable(Array(StringSource)),
                is_required=False,
                description="A list of custom ConfigMapEnvSource names from which to draw "
                "environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:"
                "https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container",
            ),
            "env_secrets": Field(
                Noneable(Array(StringSource)),
                is_required=False,
                description="A list of custom Secret names from which to draw environment "
                "variables (using ``envFrom``) for the Job. Default: ``[]``. See:"
                "https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables",
            ),
            "env_vars": Field(
                Noneable(Array(str)),
                is_required=False,
                description="A list of environment variables to inject into the Job. "
                "Default: ``[]``. See: "
                "https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables",
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
                description="A list of volume mounts to include in the job's container. Default: ``[]``. See: "
                "https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volumemount-v1-core",
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
                description="A list of volumes to include in the Job's Pod. Default: ``[]``. For the many "
                "possible volume source types that can be included, see: "
                "https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volume-v1-core",
            ),
            "labels": Field(
                dict,
                is_required=False,
                description="Labels to apply to all created pods. See: "
                "https://kubernetes.io/docs/concepts/overview/working-with-objects/labels",
            ),
            "resources": Field(
                Noneable(
                    {
                        "limits": Field(dict, is_required=False),
                        "requests": Field(dict, is_required=False),
                    }
                ),
                is_required=False,
                description="Compute resource requirements for the container. See: "
                "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
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
                    description="The namespace into which to launch Kubernetes resources. Note that any "
                    "other required resources (such as the service account) must be "
                    "present in this namespace.",
                ),
            },
        )

    @property
    def env(self) -> List[Dict[str, Optional[str]]]:
        return [{"name": key, "value": os.getenv(key)} for key in (self.env_vars or [])]

    @property
    def env_from_sources(self) -> List[Dict[str, Any]]:
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
    def from_dict(config=None):
        check.opt_dict_param(config, "config")
        return DagsterK8sJobConfig(**config)


def construct_dagster_k8s_job(
    job_config,
    args,
    job_name,
    user_defined_k8s_config=None,
    pod_name=None,
    component=None,
    labels=None,
    env_vars=None,
):
    """Constructs a Kubernetes Job object for a dagster-graphql invocation.

    Args:
        job_config (DagsterK8sJobConfig): Job configuration to use for constructing the Kubernetes
            Job object.
        args (List[str]): CLI arguments to use with dagster-graphql in this Job.
        job_name (str): The name of the Job. Note that this name must be <= 63 characters in length.
        resources (Dict[str, Dict[str, str]]): The resource requirements for the container
        pod_name (str, optional): The name of the Pod. Note that this name must be <= 63 characters
            in length. Defaults to "<job_name>-pod".
        component (str, optional): The name of the component, used to provide the Job label
            app.kubernetes.io/component. Defaults to None.
        labels(Dict[str, str]): Additional labels to be attached to k8s jobs and pod templates.
            Long label values are may be truncated.
        env_vars(Dict[str, str]): Additional environment variables to add to the K8s Container.

    Returns:
        kubernetes.client.V1Job: A Kubernetes Job object.
    """
    check.inst_param(job_config, "job_config", DagsterK8sJobConfig)
    check.list_param(args, "args", of_type=str)
    check.str_param(job_name, "job_name")
    user_defined_k8s_config = check.opt_inst_param(
        user_defined_k8s_config,
        "user_defined_k8s_config",
        UserDefinedDagsterK8sConfig,
        default=UserDefinedDagsterK8sConfig(),
    )

    pod_name = check.opt_str_param(pod_name, "pod_name", default=job_name + "-pod")
    check.opt_str_param(component, "component")
    check.opt_dict_param(env_vars, "env_vars", key_type=str, value_type=str)
    check.opt_dict_param(labels, "labels", key_type=str, value_type=str)

    check.invariant(
        len(job_name) <= MAX_K8S_NAME_LEN,
        "job_name is %d in length; Kubernetes Jobs cannot be longer than %d characters."
        % (len(job_name), MAX_K8S_NAME_LEN),
    )

    check.invariant(
        len(pod_name) <= MAX_K8S_NAME_LEN,
        "job_name is %d in length; Kubernetes Pods cannot be longer than %d characters."
        % (len(pod_name), MAX_K8S_NAME_LEN),
    )

    # See: https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/
    k8s_common_labels = {
        "app.kubernetes.io/name": "dagster",
        "app.kubernetes.io/instance": "dagster",
        "app.kubernetes.io/version": sanitize_k8s_label(dagster_version),
        "app.kubernetes.io/part-of": "dagster",
    }

    if component:
        k8s_common_labels["app.kubernetes.io/component"] = component

    additional_labels = {k: sanitize_k8s_label(v) for k, v in (labels or {}).items()}
    dagster_labels = merge_dicts(k8s_common_labels, additional_labels)

    env = [{"name": "DAGSTER_HOME", "value": job_config.dagster_home}]
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

    additional_k8s_env_vars = []
    if env_vars:
        for key, value in env_vars.items():
            additional_k8s_env_vars.append({"name": key, "value": value})

    container_config = copy.deepcopy(user_defined_k8s_config.container_config)

    user_defined_k8s_env_vars = container_config.pop("env", [])
    for env_var in user_defined_k8s_env_vars:
        additional_k8s_env_vars.append(env_var)

    user_defined_k8s_env_from = container_config.pop("env_from", [])
    additional_k8s_env_from = []
    for env_from in user_defined_k8s_env_from:
        additional_k8s_env_from.append(env_from)

    job_image = container_config.pop("image", job_config.job_image)

    user_defined_k8s_volume_mounts = container_config.pop("volume_mounts", [])

    user_defined_resources = container_config.pop("resources", {})

    volume_mounts = job_config.volume_mounts + user_defined_k8s_volume_mounts

    resources = user_defined_resources if user_defined_resources else job_config.resources

    container_config = merge_dicts(
        container_config,
        {
            "name": "dagster",
            "image": job_image,
            "args": args,
            "image_pull_policy": job_config.image_pull_policy,
            "env": env + job_config.env + additional_k8s_env_vars,
            "env_from": job_config.env_from_sources + additional_k8s_env_from,
            "volume_mounts": volume_mounts,
            "resources": resources,
        },
    )

    pod_spec_config = copy.deepcopy(user_defined_k8s_config.pod_spec_config)

    user_defined_volumes = pod_spec_config.pop("volumes", [])

    volumes = job_config.volumes + user_defined_volumes

    # If the user has defined custom labels, remove them from the pod_template_spec_metadata
    # key and merge them with the dagster labels
    pod_template_spec_metadata = copy.deepcopy(user_defined_k8s_config.pod_template_spec_metadata)
    user_defined_pod_template_labels = pod_template_spec_metadata.pop("labels", {})

    service_account_name = pod_spec_config.pop(
        "service_account_name", job_config.service_account_name
    )

    user_defined_containers = pod_spec_config.pop("containers", [])

    template = {
        "metadata": merge_dicts(
            pod_template_spec_metadata,
            {
                "name": pod_name,
                "labels": merge_dicts(
                    dagster_labels, user_defined_pod_template_labels, job_config.labels
                ),
            },
        ),
        "spec": merge_dicts(
            pod_spec_config,
            {
                "image_pull_secrets": job_config.image_pull_secrets,
                "service_account_name": service_account_name,
                "restart_policy": "Never",
                "containers": [container_config] + user_defined_containers,
                "volumes": volumes,
            },
        ),
    }

    job_spec_config = merge_dicts(
        DEFAULT_JOB_SPEC_CONFIG,
        user_defined_k8s_config.job_spec_config,
        {"template": template},
    )

    job = k8s_model_from_dict(
        kubernetes.client.V1Job,
        merge_dicts(
            user_defined_k8s_config.job_config,
            {
                "api_version": "batch/v1",
                "kind": "Job",
                "metadata": merge_dicts(
                    user_defined_k8s_config.job_metadata,
                    {"name": job_name, "labels": dagster_labels},
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
    name_hash = hashlib.md5((input_1 + input_2).encode("utf-8"))

    return name_hash.hexdigest()
