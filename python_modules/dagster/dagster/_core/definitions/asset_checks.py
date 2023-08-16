from typing import Any, Dict, Iterable, Iterator, Mapping, Set

from dagster import _check as check
from dagster._annotations import experimental, public
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_requirement import (
    ResourceAddable,
    ResourceRequirement,
    merge_resource_defs,
)


@experimental
class AssetChecksDefinition(ResourceAddable):
    _node_def: NodeDefinition
    _resource_defs: Mapping[str, ResourceDefinition]
    _specs_by_output_name: Mapping[str, AssetCheckSpec]

    def __init__(
        self,
        node_def: NodeDefinition,
        resource_defs: Mapping[str, ResourceDefinition],
        asset_keys_by_input_name: Mapping[str, AssetKey],
        specs_by_output_name: Mapping[str, AssetCheckSpec],
        # if adding new fields, make sure to handle them in the get_attributes_dict method
    ):
        self._node_def = node_def
        self._resource_defs = resource_defs
        self._asset_keys_by_input_name = check.dict_param(
            asset_keys_by_input_name, "asset_keys_by_input_name", key_type=str, value_type=AssetKey
        )
        self._specs_by_output_name = check.dict_param(
            specs_by_output_name, "specs_by_output_name", key_type=str, value_type=AssetCheckSpec
        )

    @public
    @property
    def node_def(self) -> NodeDefinition:
        """The op or op graph that can be executed to check the assets."""
        return self._node_def

    @public
    @property
    def name(self) -> str:
        return self.spec.name

    @public
    @property
    def description(self) -> str:
        return self.spec.description

    @public
    @property
    def asset_key(self) -> AssetKey:
        return self.spec.asset_key

    @public
    @property
    def spec(self) -> AssetCheckSpec:
        check.invariant(
            len(self._specs_by_output_name) == 1,
            "Tried to retrieve single-check property from a checks definition with multiple"
            " checks: "
            + ", ".join(spec.name for spec in self._specs_by_output_name.values()),
        )

        return next(iter(self.specs))

    @public
    @property
    def specs(self) -> Iterable[AssetCheckSpec]:
        return self._specs_by_output_name.values()

    @property
    def specs_by_output_name(self) -> Mapping[str, AssetCheckSpec]:
        return self._specs_by_output_name

    @property
    def asset_keys_by_input_name(self) -> Mapping[str, AssetKey]:
        return self._asset_keys_by_input_name

    def get_resource_requirements(self) -> Iterator[ResourceRequirement]:
        yield from self.node_def.get_resource_requirements()  # type: ignore[attr-defined]
        for source_key, resource_def in self._resource_defs.items():
            yield from resource_def.get_resource_requirements(outer_context=source_key)

    @public
    @property
    def required_resource_keys(self) -> Set[str]:
        """Set[str]: The set of keys for resources that must be provided to this AssetsDefinition."""
        return {requirement.key for requirement in self.get_resource_requirements()}

    def with_resources(
        self, resource_defs: Mapping[str, ResourceDefinition]
    ) -> "AssetChecksDefinition":
        attributes_dict = self.get_attributes_dict()
        attributes_dict["resource_defs"] = merge_resource_defs(
            old_resource_defs=self._resource_defs,
            resource_defs_to_merge_in=resource_defs,
            requires_resources=self,
        )
        return self.__class__(**attributes_dict)

    def get_attributes_dict(self) -> Dict[str, Any]:
        return dict(
            node_def=self._node_def,
            resource_defs=self._resource_defs,
            specs_by_output_name=self._specs_by_output_name,
            asset_keys_by_input_name=self._asset_keys_by_input_name,
        )
