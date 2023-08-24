from typing import TYPE_CHECKING

from dagster import AssetKey

from dagster_graphql.schema.asset_key import GrapheneAssetKey

from ..schema.asset_checks import (
    GrapheneAssetCheck,
    GrapheneAssetChecks,
)

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo


def fetch_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> GrapheneAssetChecks:
    external_asset_checks = []
    for location in graphene_info.context.code_locations:
        for repository in location.get_repositories().values():
            for external_check in repository.external_repository_data.external_asset_checks or []:
                if external_check.asset_key == asset_key:
                    external_asset_checks.append(external_check)

    return GrapheneAssetChecks(
        checks=[
            GrapheneAssetCheck(
                name=check.name,
                description=check.description,
                assetKey=GrapheneAssetKey(path=asset_key.path),
            )
            for check in external_asset_checks
        ]
    )
