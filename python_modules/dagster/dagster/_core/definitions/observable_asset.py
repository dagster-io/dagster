from dagster._core.definitions.asset_spec import ObservableAssetSpec
from dagster._core.definitions.decorators import asset


def create_unexecutable_observable_assets_def(observable_asset_spec: ObservableAssetSpec):
    # This function is to be used in the internals of repository definition to coerce
    # an ObservableAssetSepc into an AssetsDefinition
    # TODO: will make this use multi_asset later in the stack
    @asset(
        key=observable_asset_spec.key,
        description=observable_asset_spec.description,
        metadata=observable_asset_spec.metadata,
        group_name=observable_asset_spec.group_name,
        deps=[
            dep.asset_key for dep in observable_asset_spec.deps
        ],  # switch to not using .asset_key once jamie's diff lands
    )
    def an_asset() -> None:
        raise NotImplementedError()

    return an_asset
