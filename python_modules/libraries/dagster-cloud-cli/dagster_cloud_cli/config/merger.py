from copy import deepcopy
from typing import Any

from dagster_shared import check
from dagster_shared.utils import remove_none_recursively

from dagster_cloud_cli.config.list_merge_strategies import (
    deduplicate,
    get_list_merger_for_identifiable_dicts,
    get_list_merger_for_key_value_separated_strings,
    replace,
)
from dagster_cloud_cli.config.models import DagsterCloudYaml, Location, ProcessedDagsterCloudConfig


class DagsterCloudConfigDefaultsMerger:
    """Transform the DagsterCloudYaml provided configuration input and return the processed config resulting
    from merging the defaults with each location.
    """

    def __init__(self):
        equal_sign_list_merger = get_list_merger_for_key_value_separated_strings("=")
        named_object_list_merger = get_list_merger_for_identifiable_dicts("name")
        keyed_object_list_merger = get_list_merger_for_identifiable_dicts("key")

        self._default_list_strategy = deduplicate
        self._list_strategy_exceptions = {
            "container_context.docker.env_vars": equal_sign_list_merger,
            "container_context.ecs.env_vars": equal_sign_list_merger,
            "container_context.ecs.run_sidecar_containers": named_object_list_merger,
            "container_context.ecs.secrets": named_object_list_merger,
            "container_context.ecs.server_sidecar_containers": named_object_list_merger,
            "container_context.ecs.volumes": named_object_list_merger,
            "container_context.ecs.run_ecs_tags": keyed_object_list_merger,
            "container_context.ecs.server_ecs_tags": keyed_object_list_merger,
            "container_context.k8s.env_vars": equal_sign_list_merger,
            "container_context.k8s.image_pull_secrets": named_object_list_merger,
            "container_context.k8s.run_k8s_config.container_config.args": replace,
            "container_context.k8s.run_k8s_config.container_config.command": replace,
            "container_context.k8s.server_k8s_config.container_config.args": replace,
            "container_context.k8s.server_k8s_config.container_config.command": replace,
            "container_context.k8s.volumes": named_object_list_merger,
            "container_context.k8s.volume_mounts": named_object_list_merger,
        }

    def process(self, source_config: DagsterCloudYaml) -> ProcessedDagsterCloudConfig:
        if source_config.defaults is None:
            return ProcessedDagsterCloudConfig(locations=source_config.locations)

        source_dict = source_config.model_dump()
        return self.process_dict(source_dict)

    def process_dict(self, source_dict: dict[str, Any]) -> ProcessedDagsterCloudConfig:
        processed_config = ProcessedDagsterCloudConfig(locations=[])

        defaults = remove_none_recursively(source_dict.get("defaults", {}))
        for location in source_dict.get("locations", []):
            location_data = remove_none_recursively(location)
            if not defaults:
                processed_config.locations.append(Location.model_validate(location_data))
                continue

            transformed_location = self.merge(defaults, location_data)
            processed_config.locations.append(Location.model_validate(transformed_location))

        return processed_config

    def merge(self, onto_dict: dict[str, Any], from_dict: dict[str, Any]):
        dest = deepcopy(onto_dict)
        return self._merge_dict("", dest, from_dict)

    def _merge_dict(self, parent_key: str, onto_dict: dict[str, Any], from_dict: dict[str, Any]):
        for key, value in from_dict.items():
            key_path = ".".join([parent_key, key]) if parent_key else key
            if key in onto_dict and onto_dict[key] is not None:
                if isinstance(value, dict):
                    check.invariant(isinstance(onto_dict[key], dict))
                    onto_dict[key] = self._merge_dict(key_path, onto_dict[key], value)
                elif isinstance(value, list):
                    check.invariant(isinstance(onto_dict[key], list))
                    onto_dict[key] = self._merge_list(key_path, value, onto_dict[key])
                else:
                    onto_dict[key] = value
            else:
                onto_dict[key] = value
        return onto_dict

    def _merge_list(self, key_path: str, from_list: list[Any], onto_list: list[Any]) -> list[Any]:
        if key_path in self._list_strategy_exceptions:
            return self._list_strategy_exceptions[key_path](from_list, onto_list)

        return self._default_list_strategy(from_list, onto_list)
