from collections.abc import Mapping, Sequence

from dagster import AssetsDefinition, AssetSpec, AutomationCondition, Definitions, Nothing
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import stringify_asset_key_to_input_name
from dagster._core.definitions.input import In


def eager_asset(assets_def: AssetsDefinition) -> AssetsDefinition:
    return assets_def.map_asset_specs(
        lambda spec: spec._replace(automation_condition=AutomationCondition.eager())
        if spec.automation_condition is None
        else spec
    )


def apply_eager_automation(defs: Definitions) -> Definitions:
    assets = []
    for asset in defs.assets or []:
        if not isinstance(asset, AssetsDefinition):
            continue
        if not asset.keys:
            continue
        assets.append(
            asset.map_asset_specs(
                lambda spec: spec.replace_attributes(
                    automation_condition=AutomationCondition.eager()
                )
                if spec.automation_condition is None
                else spec
            )
        )
    return Definitions(
        assets=assets,
        asset_checks=defs.asset_checks,
        sensors=defs.sensors,
        schedules=defs.schedules,
        resources=defs.resources,
    )


def with_group(assets_def: AssetsDefinition, group_name: str) -> AssetsDefinition:
    return assets_def.map_asset_specs(lambda spec: spec.replace_attributes(group_name=group_name))


def with_deps(
    dep_map: Mapping[AssetKey, AssetKey], assets_def: AssetsDefinition
) -> AssetsDefinition:
    # dep_map is a mapping from the asset key to an asset key it depends on.
    new_deps = {}
    for key, deps in assets_def.asset_deps.items():
        new_deps[key] = set(deps)
        if key in dep_map:
            new_deps[key].add(dep_map[key])
    additional_input_names_by_key = {
        stringify_asset_key_to_input_name(dep_key): downstream_key
        for dep_key, downstream_key in dep_map.items()
    }
    complete_input_names_by_key = {**assets_def.keys_by_input_name, **additional_input_names_by_key}
    additional_ins = {
        input_name: In(dagster_type=Nothing) for input_name in additional_input_names_by_key.keys()
    }
    ins_from_input_defs = {
        input_def.name: In.from_definition(input_def)
        for input_def in assets_def.op.input_dict.values()
    }
    all_ins = {**ins_from_input_defs, **additional_ins}
    new_op = assets_def.op.with_replaced_properties(
        name=assets_def.op.name,
        ins=all_ins,
    )
    return AssetsDefinition(
        keys_by_input_name=complete_input_names_by_key,
        keys_by_output_name=assets_def.keys_by_output_name,
        node_def=new_op,
        partitions_def=assets_def.partitions_def,
        asset_deps=new_deps,
        can_subset=assets_def.can_subset,
        resource_defs=assets_def.resource_defs,
        group_names_by_key=assets_def.group_names_by_key,
        metadata_by_key=assets_def.metadata_by_key,
        tags_by_key=assets_def.tags_by_key,
        freshness_policies_by_key=assets_def.freshness_policies_by_key,
        backfill_policy=assets_def.backfill_policy,
        descriptions_by_key=assets_def.descriptions_by_key,
        check_specs_by_output_name=assets_def.check_specs_by_output_name,
        is_subset=assets_def.is_subset,
        owners_by_key=assets_def.owners_by_key,
        specs=None,
        execution_type=assets_def.execution_type,
        auto_materialize_policies_by_key=assets_def.auto_materialize_policies_by_key,
    )


def eager(specs: Sequence[AssetSpec]) -> Sequence[AssetSpec]:
    return [
        spec.replace_attributes(automation_condition=AutomationCondition.eager()) for spec in specs
    ]
