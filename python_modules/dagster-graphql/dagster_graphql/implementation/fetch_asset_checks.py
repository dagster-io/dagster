
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from ..schema.util import ResolveInfo

from dagster import AssetKey


def fetch_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
):
    for location in graphene_info.context.code_locations:
        for repository in location.get_repositories().values():
            for external_check in repository.external_repository_data.external_asset_checks or []):
                pass