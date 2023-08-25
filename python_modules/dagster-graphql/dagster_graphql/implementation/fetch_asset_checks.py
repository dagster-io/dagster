from typing import TYPE_CHECKING, Optional

from dagster import AssetKey

from ..schema.asset_checks import (
    GrapheneAssetCheck,
    GrapheneAssetChecks,
)

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo


def fetch_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    check_name: Optional[str] = None,
) -> GrapheneAssetChecks:
    external_asset_checks = []
    for location in graphene_info.context.code_locations:
        for repository in location.get_repositories().values():
            for external_check in repository.external_repository_data.external_asset_checks or []:
                if external_check.asset_key == asset_key:
                    if not check_name or check_name == external_check.name:
                        external_asset_checks.append(external_check)

    return GrapheneAssetChecks(
        checks=[
            GrapheneAssetCheck(
                name=check.name,
                description=check.description,
                asset_key=asset_key,
            )
            for check in external_asset_checks
        ]
    )
