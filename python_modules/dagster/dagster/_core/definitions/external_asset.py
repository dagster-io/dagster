from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_OBSERVE_INTERVAL_MINUTES,
    SYSTEM_METADATA_KEY_IO_MANAGER_KEY,
    AssetExecutionType,
    AssetSpec,
)
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.output import Out
from dagster._core.definitions.source_asset import (
    SourceAsset,
    wrap_source_asset_observe_fn_in_op_compute_fn,
)
from dagster._utils.warnings import disable_dagster_warnings


def create_external_asset_from_source_asset(source_asset: SourceAsset) -> AssetsDefinition:
    if source_asset.observe_fn is not None:
        keys_by_output_name = {"result": source_asset.key}
        node_def = OpDefinition.dagster_internal_init(
            name=source_asset.key.to_python_identifier(),
            compute_fn=wrap_source_asset_observe_fn_in_op_compute_fn(source_asset),
            # We need to access the raw attribute because the property will return a computed value that
            # includes requirements for the io manager. Those requirements will be inferred again when
            # we create an AssetsDefinition.
            required_resource_keys=source_asset._required_resource_keys,  # noqa: SLF001,
            ins=source_asset.op.ins,
            outs={"result": Out(io_manager_key=source_asset.io_manager_key)},
            description=source_asset.op.description,
            config_schema=source_asset.op.config_schema,
            version=None,
            retry_policy=source_asset.op.retry_policy,
            code_version=source_asset.op.version,
            pool=source_asset.op.pool,
            tags=source_asset.op_tags,
        )
        extra_metadata_entries = {}
        execution_type = AssetExecutionType.OBSERVATION
    else:
        keys_by_output_name = {}
        node_def = None
        extra_metadata_entries = (
            {SYSTEM_METADATA_KEY_IO_MANAGER_KEY: source_asset.io_manager_key}
            if source_asset.io_manager_key is not None
            else {}
        )
        execution_type = None

    observe_interval = source_asset.auto_observe_interval_minutes
    metadata = {
        **source_asset.raw_metadata,
        **extra_metadata_entries,
        **(
            {SYSTEM_METADATA_KEY_AUTO_OBSERVE_INTERVAL_MINUTES: observe_interval}
            if observe_interval
            else {}
        ),
    }

    with disable_dagster_warnings():
        spec = AssetSpec(
            key=source_asset.key,
            metadata=metadata,
            group_name=source_asset.group_name,
            description=source_asset.description,
            tags=source_asset.tags,
            legacy_freshness_policy=source_asset.legacy_freshness_policy,
            automation_condition=source_asset.automation_condition,
            deps=[],
            owners=[],
            partitions_def=source_asset.partitions_def,
        )

        return AssetsDefinition(
            specs=[spec],
            keys_by_output_name=keys_by_output_name,
            node_def=node_def,
            # We don't pass the `io_manager_def` because it will already be present in
            # `resource_defs` (it is added during `SourceAsset` initialization).
            resource_defs=source_asset.resource_defs,
            execution_type=execution_type,
        )


# Create an unexecutable assets def from an existing executable assets def. This is used to make a
# materializable assets def available only for loading in a job.
def create_unexecutable_external_asset_from_assets_def(
    assets_def: AssetsDefinition,
) -> AssetsDefinition:
    if not assets_def.is_executable:
        return assets_def
    else:
        with disable_dagster_warnings():
            specs: list[AssetSpec] = []
            # Important to iterate over assets_def.keys here instead of assets_def.specs. This is
            # because assets_def.specs on an AssetsDefinition that is a subset will contain all the
            # specs of its parent.
            for key in assets_def.keys:
                orig_spec = assets_def.get_asset_spec(key)
                specs.append(
                    orig_spec.merge_attributes(
                        metadata=(
                            {
                                SYSTEM_METADATA_KEY_IO_MANAGER_KEY: assets_def.get_io_manager_key_for_asset_key(
                                    key
                                )
                            }
                            if assets_def.has_output_for_asset_key(key)
                            else {}
                        ),
                    ).replace_attributes(
                        automation_condition=None,
                    )
                )
            return AssetsDefinition(
                specs=specs,
                resource_defs=assets_def.resource_defs,
            )
