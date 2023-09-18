from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators import asset
from dagster._core.errors import DagsterInvariantViolationError


def create_unexecutable_observable_assets_def(asset_spec: AssetSpec):
    # This function is to be used in the internals of repository definition to coerce
    # an AssetSpec into an AssetsDefinition
    # TODO: will make this use multi_asset later in the stack
    @asset(
        key=asset_spec.key,
        description=asset_spec.description,
        metadata=asset_spec.metadata,
        group_name=asset_spec.group_name,
        deps=[
            dep.asset_key for dep in asset_spec.deps
        ],  # switch to not using .asset_key once jamie's diff lands
    )
    def an_asset() -> None:
        raise DagsterInvariantViolationError(
            f"You have attempted to execute an unexecutable asset {asset_spec.key}"
        )

    return an_asset
