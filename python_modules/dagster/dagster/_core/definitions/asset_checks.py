from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Iterator,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
)

from dagster import _check as check
from dagster._annotations import experimental, public
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_requirement import (
    RequiresResources,
    ResourceAddable,
    ResourceRequirement,
    merge_resource_defs,
)
from dagster._core.errors import DagsterAssetCheckFailedError

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition


@experimental
class AssetChecksDefinitionInputOutputProps(NamedTuple):
    asset_check_keys_by_output_name: Mapping[str, AssetCheckKey]
    asset_keys_by_input_name: Mapping[str, AssetKey]


@experimental
class AssetChecksDefinition(ResourceAddable, RequiresResources):
    """Defines a set of checks that are produced by the same op or op graph.

    AssetChecksDefinition are typically not instantiated directly, but rather produced using a
    decorator like :py:func:`@asset_check <asset>`.
    """

    def __init__(
        self,
        *,
        node_def: NodeDefinition,
        resource_defs: Mapping[str, ResourceDefinition],
        specs: Sequence[AssetCheckSpec],
        input_output_props: AssetChecksDefinitionInputOutputProps
        # if adding new fields, make sure to handle them in the get_attributes_dict method
    ):
        self._node_def = node_def
        self._resource_defs = resource_defs
        self._specs = check.sequence_param(specs, "specs", of_type=AssetCheckSpec)
        self._input_output_props = check.inst_param(
            input_output_props, "input_output_props", AssetChecksDefinitionInputOutputProps
        )
        self._specs_by_handle = {spec.key: spec for spec in specs}
        self._specs_by_output_name = {
            output_name: self._specs_by_handle[check_key]
            for output_name, check_key in input_output_props.asset_check_keys_by_output_name.items()
        }

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
    def description(self) -> Optional[str]:
        return self.spec.description

    @public
    @property
    def asset_key(self) -> AssetKey:
        return self.spec.asset_key

    @public
    @property
    def spec(self) -> AssetCheckSpec:
        if len(self._specs_by_output_name) > 1:
            check.failed(
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
        return self._input_output_props.asset_keys_by_input_name

    def get_resource_requirements(self) -> Iterator[ResourceRequirement]:
        yield from self.node_def.get_resource_requirements()  # type: ignore[attr-defined]
        for source_key, resource_def in self._resource_defs.items():
            yield from resource_def.get_resource_requirements(outer_context=source_key)

    def get_spec_for_check_key(self, asset_check_key: AssetCheckKey) -> AssetCheckSpec:
        return self._specs_by_handle[asset_check_key]

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
            specs=self._specs,
            input_output_props=self._input_output_props,
        )


@experimental
def build_blocking_asset_check(
    asset_def: "AssetsDefinition",
    checks: Sequence[AssetChecksDefinition],
) -> "AssetsDefinition":
    from dagster import In, Output, graph_asset, op


    check_specs = []
    for c in checks:
        check_specs.extend(c.specs)

    check_output_names = [c.get_python_identifier() for c in check_specs]

    @op(ins={"materialization": In(Any), "check_evaluations": In(Any)})
    def fan_in_checks_and_materialization(context, materialization, check_evaluations):
        yield Output(materialization)

        for result in check_evaluations:
            if not result.success:
                raise DagsterAssetCheckFailedError()

    @graph_asset(
        name=asset_def.key.path[-1],
        key_prefix=asset_def.key.path[:-1] if len(asset_def.key.path) > 1 else None,
        check_specs=check_specs,
        # if we don't rename the graph, it will conflict with asset_def's Op
        _graph_name=asset_def.key.to_python_identifier() + "_blocking_asset_check",
    )
    def blocking_asset():
        asset_result = asset_def.op()
        check_evaluations = [check.node_def(asset_result) for check in checks]

        return {
            "result": fan_in_checks_and_materialization(asset_result, check_evaluations),
            **{
                check_output_name: check_result
                for check_output_name, check_result in zip(check_output_names, check_evaluations)
            },
        }

    return blocking_asset
