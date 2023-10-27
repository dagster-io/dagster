import copy
from typing import TYPE_CHECKING, Any, Dict, Mapping, NamedTuple, Optional, Sequence, cast

import dagster._check as check
import kubernetes
import kubernetes.client
from dagster._config import process_config
from dagster._core.container_context import process_shared_container_context_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.utils import parse_env_var
from dagster._utils import hash_collection

if TYPE_CHECKING:
    from . import K8sRunLauncher

from .job import (
    DagsterK8sJobConfig,
    K8sConfigMergeBehavior,
    UserDefinedDagsterK8sConfig,
    get_user_defined_k8s_config,
)
from .models import k8s_snake_case_dict


def _dedupe_list(values):
    new_list = []
    hashes = set()
    for value in values:
        value_hash = hash_collection(value) if isinstance(value, (list, dict)) else hash(value)
        if value_hash not in hashes:
            hashes.add(value_hash)
            new_list.append(value)

    return new_list


# Lists that don't make sense to append when they're set from two different raw k8s configs,
# even if deep-merging
ALWAYS_SHALLOW_MERGE_LIST_FIELDS = {
    "command",
    "args",
}


class K8sContainerContext(
    NamedTuple(
        "_K8sContainerContext",
        [
            ("image_pull_policy", Optional[str]),
            ("image_pull_secrets", Sequence[Mapping[str, str]]),
            ("service_account_name", Optional[str]),
            ("env_config_maps", Sequence[str]),
            ("env_secrets", Sequence[str]),
            ("env_vars", Sequence[str]),
            ("volume_mounts", Sequence[Mapping[str, Any]]),
            ("volumes", Sequence[Mapping[str, Any]]),
            ("labels", Mapping[str, str]),
            ("namespace", Optional[str]),
            ("resources", Mapping[str, Any]),
            ("scheduler_name", Optional[str]),
            ("security_context", Mapping[str, Any]),
            ("server_k8s_config", UserDefinedDagsterK8sConfig),
            ("run_k8s_config", UserDefinedDagsterK8sConfig),
            ("env", Sequence[Mapping[str, Any]]),
        ],
    )
):
    """Encapsulates configuration that can be applied to a K8s job running Dagster code.
    Can be persisted on a DagsterRun at run submission time based on metadata from the
    code location and then included in the job's configuration at run launch time or step
    launch time.
    """

    def __new__(
        cls,
        image_pull_policy: Optional[str] = None,
        image_pull_secrets: Optional[Sequence[Mapping[str, str]]] = None,
        service_account_name: Optional[str] = None,
        env_config_maps: Optional[Sequence[str]] = None,
        env_secrets: Optional[Sequence[str]] = None,
        env_vars: Optional[Sequence[str]] = None,
        volume_mounts: Optional[Sequence[Mapping[str, Any]]] = None,
        volumes: Optional[Sequence[Mapping[str, Any]]] = None,
        labels: Optional[Mapping[str, str]] = None,
        namespace: Optional[str] = None,
        resources: Optional[Mapping[str, Any]] = None,
        scheduler_name: Optional[str] = None,
        security_context: Optional[Mapping[str, Any]] = None,
        server_k8s_config: Optional[UserDefinedDagsterK8sConfig] = None,
        run_k8s_config: Optional[UserDefinedDagsterK8sConfig] = None,
        env: Optional[Sequence[Mapping[str, Any]]] = None,
    ):
        return super(K8sContainerContext, cls).__new__(
            cls,
            image_pull_policy=check.opt_str_param(image_pull_policy, "image_pull_policy"),
            image_pull_secrets=check.opt_sequence_param(image_pull_secrets, "image_pull_secrets"),
            service_account_name=check.opt_str_param(service_account_name, "service_account_name"),
            env_config_maps=check.opt_sequence_param(env_config_maps, "env_config_maps"),
            env_secrets=check.opt_sequence_param(env_secrets, "env_secrets"),
            env_vars=check.opt_sequence_param(env_vars, "env_vars"),
            volume_mounts=[
                k8s_snake_case_dict(kubernetes.client.V1VolumeMount, mount)
                for mount in check.opt_sequence_param(volume_mounts, "volume_mounts")
            ],
            volumes=[
                k8s_snake_case_dict(kubernetes.client.V1Volume, volume)
                for volume in check.opt_sequence_param(volumes, "volumes")
            ],
            labels=check.opt_mapping_param(labels, "labels"),
            namespace=check.opt_str_param(namespace, "namespace"),
            resources=check.opt_mapping_param(resources, "resources"),
            scheduler_name=check.opt_str_param(scheduler_name, "scheduler_name"),
            security_context=check.opt_mapping_param(security_context, "security_context"),
            server_k8s_config=server_k8s_config or UserDefinedDagsterK8sConfig.from_dict({}),
            run_k8s_config=run_k8s_config or UserDefinedDagsterK8sConfig.from_dict({}),
            env=[
                k8s_snake_case_dict(kubernetes.client.V1EnvVar, e)
                for e in check.opt_sequence_param(env, "env")
            ],
        )

    def _merge_k8s_config(
        self,
        onto_config: UserDefinedDagsterK8sConfig,
        from_config: UserDefinedDagsterK8sConfig,
    ) -> UserDefinedDagsterK8sConfig:
        # Keys are always the same and initialized in constructor
        merge_behavior = from_config.merge_behavior
        onto_dict = onto_config.to_dict()
        from_dict = from_config.to_dict()
        assert set(onto_dict) == set(from_dict)
        if merge_behavior == K8sConfigMergeBehavior.DEEP:
            onto_dict = copy.deepcopy(onto_dict)
            merged_dict = self._deep_merge_k8s_config(onto_dict=onto_dict, from_dict=from_dict)
        else:
            merged_dict = {
                key: (
                    {**onto_dict[key], **from_dict[key]}
                    if isinstance(onto_dict[key], dict)
                    else from_dict[key]
                )
                for key in onto_dict
            }
        return UserDefinedDagsterK8sConfig.from_dict(merged_dict)

    def _deep_merge_k8s_config(self, onto_dict: Dict[str, Any], from_dict: Mapping[str, Any]):
        for from_key, from_value in from_dict.items():
            if from_key not in onto_dict:
                onto_dict[from_key] = from_value

            else:
                onto_value = onto_dict[from_key]

                if (
                    isinstance(from_value, list)
                    and from_key not in ALWAYS_SHALLOW_MERGE_LIST_FIELDS
                ):
                    check.invariant(isinstance(onto_value, list))
                    onto_dict[from_key] = _dedupe_list([*onto_value, *from_value])
                elif isinstance(from_value, dict):
                    check.invariant(isinstance(onto_value, dict))
                    onto_dict[from_key] = self._deep_merge_k8s_config(onto_value, from_value)
                else:
                    onto_dict[from_key] = from_value
        return onto_dict

    def merge(
        self,
        other: "K8sContainerContext",
    ) -> "K8sContainerContext":
        # Lists of attributes that can be combined are combined, scalar values are replaced
        # prefering the passed in container context
        return K8sContainerContext(
            image_pull_policy=(
                other.image_pull_policy if other.image_pull_policy else self.image_pull_policy
            ),
            image_pull_secrets=_dedupe_list([*self.image_pull_secrets, *other.image_pull_secrets]),
            service_account_name=(
                other.service_account_name
                if other.service_account_name
                else self.service_account_name
            ),
            env_config_maps=_dedupe_list([*self.env_config_maps, *other.env_config_maps]),
            env_secrets=_dedupe_list([*self.env_secrets, *other.env_secrets]),
            env_vars=_dedupe_list([*self.env_vars, *other.env_vars]),
            volume_mounts=_dedupe_list([*self.volume_mounts, *other.volume_mounts]),
            volumes=_dedupe_list([*self.volumes, *other.volumes]),
            labels={**self.labels, **other.labels},
            namespace=other.namespace if other.namespace else self.namespace,
            resources=other.resources if other.resources else self.resources,
            scheduler_name=other.scheduler_name if other.scheduler_name else self.scheduler_name,
            security_context=(
                other.security_context if other.security_context else self.security_context
            ),
            server_k8s_config=self._merge_k8s_config(
                self.server_k8s_config, other.server_k8s_config
            ),
            run_k8s_config=self._merge_k8s_config(self.run_k8s_config, other.run_k8s_config),
            env=_dedupe_list([*self.env, *other.env]),
        )

    def get_environment_dict(self) -> Mapping[str, str]:
        parsed_env_var_tuples = [parse_env_var(env_var) for env_var in self.env_vars]
        return {env_var_tuple[0]: env_var_tuple[1] for env_var_tuple in parsed_env_var_tuples}

    @staticmethod
    def create_for_run(
        dagster_run: DagsterRun,
        run_launcher: Optional["K8sRunLauncher"],
        include_run_tags: bool,
    ) -> "K8sContainerContext":
        context = K8sContainerContext()

        if run_launcher:
            context = context.merge(
                K8sContainerContext(
                    image_pull_policy=run_launcher.image_pull_policy,
                    image_pull_secrets=run_launcher.image_pull_secrets,
                    service_account_name=run_launcher.service_account_name,
                    env_config_maps=run_launcher.env_config_maps,
                    env_secrets=run_launcher.env_secrets,
                    env_vars=run_launcher.env_vars,
                    volume_mounts=run_launcher.volume_mounts,
                    volumes=run_launcher.volumes,
                    labels=run_launcher.labels,
                    namespace=run_launcher.job_namespace,
                    resources=run_launcher.resources,
                    scheduler_name=run_launcher.scheduler_name,
                    security_context=run_launcher.security_context,
                    run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                        run_launcher.run_k8s_config or {}
                    ),
                )
            )

        if dagster_run.job_code_origin:
            run_container_context = dagster_run.job_code_origin.repository_origin.container_context

            if run_container_context:
                context = context.merge(
                    K8sContainerContext.create_from_config(run_container_context)
                )

        if include_run_tags:
            user_defined_k8s_config = get_user_defined_k8s_config(dagster_run.tags)

            context = context.merge(K8sContainerContext(run_k8s_config=user_defined_k8s_config))

        return context

    @staticmethod
    def create_from_config(run_container_context) -> "K8sContainerContext":
        processed_shared_container_context = process_shared_container_context_config(
            run_container_context or {}
        )
        shared_container_context = K8sContainerContext(
            env_vars=processed_shared_container_context.get("env_vars", [])
        )

        run_k8s_container_context = (
            run_container_context.get("k8s", {}) if run_container_context else {}
        )

        if not run_k8s_container_context:
            return shared_container_context

        processed_container_context = process_config(
            DagsterK8sJobConfig.config_type_container_context(), run_k8s_container_context
        )

        if not processed_container_context.success:
            raise DagsterInvalidConfigError(
                "Errors while parsing k8s container context",
                processed_container_context.errors,
                run_k8s_container_context,
            )

        processed_context_value = cast(Dict, processed_container_context.value)

        return shared_container_context.merge(
            K8sContainerContext(
                image_pull_policy=processed_context_value.get("image_pull_policy"),
                image_pull_secrets=processed_context_value.get("image_pull_secrets"),
                service_account_name=processed_context_value.get("service_account_name"),
                env_config_maps=processed_context_value.get("env_config_maps"),
                env_secrets=processed_context_value.get("env_secrets"),
                env_vars=processed_context_value.get("env_vars"),
                volume_mounts=processed_context_value.get("volume_mounts"),
                volumes=processed_context_value.get("volumes"),
                labels=processed_context_value.get("labels"),
                namespace=processed_context_value.get("namespace"),
                resources=processed_context_value.get("resources"),
                scheduler_name=processed_context_value.get("scheduler_name"),
                security_context=processed_context_value.get("security_context"),
                server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                    processed_context_value.get("server_k8s_config", {})
                ),
                run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                    processed_context_value.get("run_k8s_config", {})
                ),
                env=processed_context_value.get("env"),
            ),
        )

    def get_k8s_job_config(self, job_image, run_launcher) -> DagsterK8sJobConfig:
        return DagsterK8sJobConfig(
            job_image=job_image if job_image else run_launcher.job_image,
            dagster_home=run_launcher.dagster_home,
            image_pull_policy=self.image_pull_policy,
            image_pull_secrets=self.image_pull_secrets,
            service_account_name=self.service_account_name,
            instance_config_map=run_launcher.instance_config_map,
            postgres_password_secret=run_launcher.postgres_password_secret,
            env_config_maps=self.env_config_maps,
            env_secrets=self.env_secrets,
            env_vars=self.env_vars,
            volume_mounts=self.volume_mounts,
            volumes=self.volumes,
            labels=self.labels,
            resources=self.resources,
            scheduler_name=self.scheduler_name,
            security_context=self.security_context,
        )
