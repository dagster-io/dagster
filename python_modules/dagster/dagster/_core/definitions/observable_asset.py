from dagster._core.definitions.asset_spec import ObservableAssetSpec
from dagster._core.definitions.decorators import asset


def create_observable_asset(observable_asset_spec: ObservableAssetSpec):
    @asset(
        key=observable_asset_spec.key,
        description=observable_asset_spec.description,
        metadata=observable_asset_spec.metadata,
        group_name=observable_asset_spec.group_name,
        deps=[
            dep.asset_key for dep in observable_asset_spec.deps
        ],  # switch to deps once jamie's diff lands
    )
    def an_asset() -> None:
        raise NotImplementedError()

    return an_asset
