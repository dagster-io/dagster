import copy
import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, cast

import dagster._check as check
import kubernetes
import kubernetes.client
from dagster._config import process_config
from dagster._core.container_context import process_shared_container_context_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.utils import parse_env_var
from dagster_shared.utils.hash import hash_collection

if TYPE_CHECKING:
    from dagster_k8s import K8sRunLauncher

from dagster_k8s.job import (
    DagsterK8sJobConfig,
    K8sConfigMergeBehavior,
    UserDefinedDagsterK8sConfig,
    get_user_defined_k8s_config,
)
from dagster_k8s.models import k8s_snake_case_dict, k8s_snake_case_keys


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
            ("server_k8s_config", UserDefinedDagsterK8sConfig),
            ("run_k8s_config", UserDefinedDagsterK8sConfig),
            ("namespace", Optional[str]),
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
        top_level_k8s_config = K8sContainerContext._get_base_user_defined_k8s_config(
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
            resources=check.opt_mapping_param(resources, "resources"),
            scheduler_name=check.opt_str_param(scheduler_name, "scheduler_name"),
            security_context=check.opt_mapping_param(security_context, "security_context"),
            env=[
                k8s_snake_case_dict(kubernetes.client.V1EnvVar, e)
                for e in check.opt_sequence_param(env, "env")
            ],
        )

        run_k8s_config = K8sContainerContext._merge_k8s_config(
            top_level_k8s_config._replace(  # remove k8s service/deployment fields
                deployment_metadata={},
                service_metadata={},
            ),
            run_k8s_config or UserDefinedDagsterK8sConfig.from_dict({}),
        )

        server_k8s_config = K8sContainerContext._merge_k8s_config(
            top_level_k8s_config._replace(  # remove k8s job fields
                job_config={},
                job_metadata={},
                job_spec_config={},
            ),
            server_k8s_config or UserDefinedDagsterK8sConfig.from_dict({}),
        )

        return super().__new__(
            cls,
            run_k8s_config=run_k8s_config,
            server_k8s_config=server_k8s_config,
            namespace=namespace,
        )

    @staticmethod
    def _get_base_user_defined_k8s_config(
        image_pull_policy: Optional[str],
        image_pull_secrets: Optional[Sequence[Mapping[str, str]]],
        service_account_name: Optional[str],
        env_config_maps: Sequence[str],
        env_secrets: Sequence[str],
        env_vars: Sequence[str],
        volume_mounts: Sequence[Mapping[str, Any]],
        volumes: Sequence[Mapping[str, Any]],
        labels: Mapping[str, str],
        resources: Mapping[str, Any],
        scheduler_name: Optional[str],
        security_context: Mapping[str, Any],
        env: Sequence[Mapping[str, Any]],
    ) -> UserDefinedDagsterK8sConfig:
        container_config = {}
        pod_spec_config = {}
        pod_template_spec_metadata = {}
        job_metadata = {}
        deployment_metadata = {}
        service_metadata = {}

        if volume_mounts:
            container_config["volume_mounts"] = volume_mounts

        if resources:
            container_config["resources"] = resources

        if image_pull_secrets:
            pod_spec_config["image_pull_secrets"] = image_pull_secrets

        if volumes:
            pod_spec_config["volumes"] = volumes

        if labels:
            pod_template_spec_metadata["labels"] = labels
            job_metadata["labels"] = labels
            deployment_metadata["labels"] = labels
            service_metadata["labels"] = labels

        if image_pull_policy:
            container_config["image_pull_policy"] = image_pull_policy

        if service_account_name:
            pod_spec_config["service_account_name"] = service_account_name

        env_from = [{"config_map_ref": {"name": config_map}} for config_map in env_config_maps]

        env_from.extend([{"secret_ref": {"name": secret}} for secret in env_secrets])

        if env_from:
            container_config["env_from"] = env_from

        parsed_env_vars = [parse_env_var(key) for key in env_vars]

        container_config_env = [
            {"name": parsed_env_var[0], "value": parsed_env_var[1]}
            for parsed_env_var in parsed_env_vars
        ]

        container_config_env.extend([{**v} for v in env])

        if container_config_env:
            container_config["env"] = container_config_env

        if scheduler_name:
            pod_spec_config["scheduler_name"] = scheduler_name

        if security_context:
            container_config["security_context"] = security_context

        return UserDefinedDagsterK8sConfig(
            container_config=container_config,
            pod_spec_config=pod_spec_config,
            pod_template_spec_metadata=pod_template_spec_metadata,
            job_metadata=job_metadata,
            service_metadata=service_metadata,
            deployment_metadata=deployment_metadata,
        )

    @staticmethod
    def _merge_k8s_config(
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
            merged_dict = K8sContainerContext._deep_merge_k8s_config(
                onto_dict=onto_dict, from_dict=from_dict
            )
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

    @staticmethod
    def _deep_merge_k8s_config(onto_dict: dict[str, Any], from_dict: Mapping[str, Any]):
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
                    onto_dict[from_key] = K8sContainerContext._deep_merge_k8s_config(
                        onto_value, from_value
                    )
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
            server_k8s_config=self._merge_k8s_config(
                self.server_k8s_config, other.server_k8s_config
            ),
            run_k8s_config=self._merge_k8s_config(self.run_k8s_config, other.run_k8s_config),
            namespace=other.namespace if other.namespace else self.namespace,
        )

    def _snake_case_allowed_fields(
        self, only_allow_user_defined_k8s_config_fields: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        result = {}

        for key in only_allow_user_defined_k8s_config_fields:
            if key == "namespace":
                result[key] = only_allow_user_defined_k8s_config_fields[key]
                continue

            if key == "container_config":
                model_class = kubernetes.client.V1Container
            elif key in {
                "job_metadata",
                "pod_template_spec_metadata",
                "deployment_metadata",
                "service_metadata",
            }:
                model_class = kubernetes.client.V1ObjectMeta
            elif key == "pod_spec_config":
                model_class = kubernetes.client.V1PodSpec
            elif key == "job_spec_config":
                model_class = kubernetes.client.V1JobSpec
            else:
                raise Exception(f"Unexpected key in allowlist {key}")
            result[key] = k8s_snake_case_keys(
                model_class, only_allow_user_defined_k8s_config_fields[key]
            )
        return result

    def validate_user_k8s_config_for_run(
        self,
        only_allow_user_defined_k8s_config_fields: Optional[Mapping[str, Any]],
        only_allow_user_defined_env_vars: Optional[Sequence[str]],
    ):
        return self._validate_user_k8s_config(
            self.run_k8s_config,
            only_allow_user_defined_k8s_config_fields,
            only_allow_user_defined_env_vars,
        )

    def validate_user_k8s_config_for_code_server(
        self,
        only_allow_user_defined_k8s_config_fields: Optional[Mapping[str, Any]],
        only_allow_user_defined_env_vars: Optional[Sequence[str]],
    ):
        return self._validate_user_k8s_config(
            self.server_k8s_config,
            only_allow_user_defined_k8s_config_fields,
            only_allow_user_defined_env_vars,
        )

    def _validate_user_k8s_config(
        self,
        user_defined_k8s_config: UserDefinedDagsterK8sConfig,
        only_allow_user_defined_k8s_config_fields: Optional[Mapping[str, Any]],
        only_allow_user_defined_env_vars: Optional[Sequence[str]],
    ) -> "K8sContainerContext":
        used_fields = self._get_used_k8s_config_fields(user_defined_k8s_config)

        if only_allow_user_defined_k8s_config_fields is not None:
            snake_case_allowlist = self._snake_case_allowed_fields(
                only_allow_user_defined_k8s_config_fields
            )

            disallowed_fields = []

            for key, used_fields_with_key in used_fields.items():
                if isinstance(used_fields_with_key, set):
                    for used_field in used_fields_with_key:
                        if not snake_case_allowlist.get(key, {}).get(used_field):
                            disallowed_fields.append(f"{key}.{used_field}")
                else:
                    check.invariant(isinstance(used_fields_with_key, bool))
                    if used_fields_with_key and not only_allow_user_defined_k8s_config_fields.get(
                        key
                    ):
                        disallowed_fields.append(key)

            if disallowed_fields:
                raise Exception(
                    f"Attempted to create a pod with fields that violated the allowed list: {', '.join(disallowed_fields)}"
                )

        validated_container_context = self

        if only_allow_user_defined_env_vars is not None:
            validated_container_context = self._filter_user_defined_env_vars(
                set(only_allow_user_defined_env_vars)
            )

        return validated_container_context

    def _filter_user_defined_k8s_config_env_vars(
        self,
        user_defined_k8s_config: UserDefinedDagsterK8sConfig,
        only_allow_user_defined_env_vars: set[str],
        discarded_env_var_names: set[str],
    ) -> UserDefinedDagsterK8sConfig:
        """Filters out any env vars from the supplied UserDefinedDagsterK8sConfig
        that are not in the supplied set of env var names and adds the names of
        any env vars that were discarded to the passed-in discarded_env_var_names set.
        """
        if "env" not in user_defined_k8s_config.container_config:
            return user_defined_k8s_config

        filtered_env = []
        for env_dict in user_defined_k8s_config.container_config["env"]:
            env_key = env_dict["name"]
            if env_key in only_allow_user_defined_env_vars:
                filtered_env.append(env_dict)
            else:
                discarded_env_var_names.add(env_key)

        return UserDefinedDagsterK8sConfig.from_dict(
            {
                **user_defined_k8s_config.to_dict(),
                "container_config": {
                    **user_defined_k8s_config.container_config,
                    "env": filtered_env,
                },
            }
        )

    def _filter_user_defined_env_vars(
        self,
        only_allow_user_defined_env_vars: set[str],
    ) -> "K8sContainerContext":
        discarded_env_var_names = set()

        new_run_k8s_config = self._filter_user_defined_k8s_config_env_vars(
            self.run_k8s_config,
            only_allow_user_defined_env_vars,
            discarded_env_var_names,
        )

        new_server_k8s_config = self._filter_user_defined_k8s_config_env_vars(
            self.server_k8s_config,
            only_allow_user_defined_env_vars,
            discarded_env_var_names,
        )

        if discarded_env_var_names:
            logging.warning(
                f"Excluding the following environment variables because they are not in the allowlist for user-defined environment variables: {', '.join(discarded_env_var_names)}"
            )

        return self._replace(
            run_k8s_config=new_run_k8s_config,
            server_k8s_config=new_server_k8s_config,
        )

    def _get_used_k8s_config_fields(
        self, user_defined_k8s_config: UserDefinedDagsterK8sConfig
    ) -> Mapping[str, Mapping[str, set[str]]]:
        used_fields = {}
        for key, fields in user_defined_k8s_config.to_dict().items():
            if key == "merge_behavior":
                continue

            used_fields[key] = used_fields.get(key, set()).union(
                {field_key for field_key in fields}
            )

        if self.namespace:
            used_fields["namespace"] = True

        return used_fields

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

        user_defined_container_context = K8sContainerContext()

        if dagster_run.job_code_origin:
            run_container_context = dagster_run.job_code_origin.repository_origin.container_context

            if run_container_context:
                user_defined_container_context = user_defined_container_context.merge(
                    K8sContainerContext.create_from_config(run_container_context)
                )

        if include_run_tags:
            user_defined_k8s_config = get_user_defined_k8s_config(dagster_run.tags)

            user_defined_container_context = user_defined_container_context.merge(
                K8sContainerContext(run_k8s_config=user_defined_k8s_config)
            )

        # If there's an allowlist, make sure user_defined_container_context doesn't violate it
        if run_launcher:
            user_defined_container_context = (
                user_defined_container_context.validate_user_k8s_config_for_run(
                    run_launcher.only_allow_user_defined_k8s_config_fields,
                    run_launcher.only_allow_user_defined_env_vars,
                )
            )

        return context.merge(user_defined_container_context)

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

        processed_context_value = cast(dict, processed_container_context.value)

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
            instance_config_map=run_launcher.instance_config_map,
            postgres_password_secret=run_launcher.postgres_password_secret,
        )
