from typing import Iterable, Iterator, List, Mapping, Optional, Tuple

from dagster import (
    _check as check,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.host_representation.code_location import CodeLocation
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.external_data import ExternalAssetCheck
from dagster._core.storage.asset_check_execution_record import AssetCheckInstanceSupport
from dagster._core.workspace.context import WorkspaceRequestContext
from packaging import version

from dagster_graphql.schema.asset_checks import (
    AssetChecksOrErrorUnion,
    GrapheneAssetCheck,
    GrapheneAssetCheckCanExecuteIndividually,
    GrapheneAssetCheckNeedsAgentUpgradeError,
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
    GrapheneAssetChecks,
)

from .fetch_assets import repository_iter


def asset_checks_iter(
    context: WorkspaceRequestContext
) -> Iterator[Tuple[CodeLocation, ExternalRepository, ExternalAssetCheck]]:
    for location, repository in repository_iter(context):
        for external_check in repository.external_repository_data.external_asset_checks or []:
            yield (location, repository, external_check)


class AssetChecksLoader:
    """A batch loader that fetches asset check definitions for a set of asset keys."""

    def __init__(self, context: WorkspaceRequestContext, asset_keys: Iterable[AssetKey]):
        self._context = context
        self._asset_keys = list(asset_keys)
        self._checks: Optional[Mapping[AssetKey, AssetChecksOrErrorUnion]] = None

    def _fetch_checks(self) -> Mapping[AssetKey, AssetChecksOrErrorUnion]:
        instance = self._context.instance
        asset_check_support = instance.get_asset_check_support()
        if asset_check_support == AssetCheckInstanceSupport.NEEDS_MIGRATION:
            return {
                asset_key: GrapheneAssetCheckNeedsMigrationError(
                    message="Asset checks require an instance migration. Run `dagster instance migrate`."
                )
                for asset_key in self._asset_keys
            }
        elif asset_check_support == AssetCheckInstanceSupport.NEEDS_AGENT_UPGRADE:
            return {
                asset_key: GrapheneAssetCheckNeedsAgentUpgradeError(
                    "Asset checks require an agent upgrade to 1.5.0 or greater."
                )
                for asset_key in self._asset_keys
            }
        else:
            check.invariant(
                asset_check_support == AssetCheckInstanceSupport.SUPPORTED,
                f"Unexpected asset check support status {asset_check_support}",
            )

        external_checks: Mapping[AssetKey, List[ExternalAssetCheck]] = {}
        errors: Mapping[AssetKey, GrapheneAssetCheckNeedsUserCodeUpgrade] = {}

        for location, _, external_check in asset_checks_iter(self._context):
            if external_check.asset_key in self._asset_keys:
                # check if the code location is too old to support executing asset checks individually
                code_location_version = (location.get_dagster_library_versions() or {}).get(
                    "dagster"
                )
                if code_location_version and version.parse(code_location_version) < version.parse(
                    "1.5"
                ):
                    errors[external_check.asset_key] = GrapheneAssetCheckNeedsUserCodeUpgrade(
                        message=(
                            "Asset checks require dagster>=1.5. Upgrade your dagster"
                            " version for this code location."
                        )
                    )
                else:
                    external_checks.setdefault(external_check.asset_key, []).append(external_check)

        asset_graph = ExternalAssetGraph.from_workspace(self._context)

        graphene_checks: Mapping[AssetKey, AssetChecksOrErrorUnion] = {}
        for asset_key in self._asset_keys:
            if asset_key in errors:
                graphene_checks[asset_key] = errors[asset_key]
            else:
                checks = []
                for external_check in external_checks.get(asset_key, []):
                    can_execute_individually = (
                        GrapheneAssetCheckCanExecuteIndividually.CAN_EXECUTE
                        if len(
                            asset_graph.get_required_asset_and_check_keys(external_check.key) or []
                        )
                        <= 1
                        # NOTE: once we support multi checks, we'll need to add a case for
                        # non subsettable multi checks
                        else GrapheneAssetCheckCanExecuteIndividually.REQUIRES_MATERIALIZATION
                    )
                    checks.append(
                        GrapheneAssetCheck(
                            asset_check=external_check,
                            can_execute_individually=can_execute_individually,
                        )
                    )
                graphene_checks[asset_key] = GrapheneAssetChecks(checks=checks)

        return graphene_checks

    def get_checks_for_asset(self, asset_key: AssetKey) -> AssetChecksOrErrorUnion:
        if self._checks is None:
            self._checks = self._fetch_checks()

        check.invariant(
            asset_key in self._checks, f"Asset key {asset_key} not included in this loader."
        )

        return self._checks[asset_key]
