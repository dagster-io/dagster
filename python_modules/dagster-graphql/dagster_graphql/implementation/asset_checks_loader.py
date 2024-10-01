from typing import Iterable, Iterator, List, Mapping, Optional, Tuple, cast

from dagster import _check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.selector import RepositorySelector
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import AssetCheckNodeSnap
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
    AssetCheckInstanceSupport,
)
from dagster._core.storage.dagster_run import RunRecord
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
from dagster_graphql.schema.inputs import GraphenePipelineSelector


class AssetChecksLoader:
    """A batch loader that fetches asset check definitions for a set of asset keys."""

    def __init__(self, context: WorkspaceRequestContext, asset_keys: Iterable[AssetKey]):
        self._context = context
        self._asset_keys = list(asset_keys)
        self._checks: Optional[Mapping[AssetKey, AssetChecksOrErrorUnion]] = None
        self._limit_per_asset = None
        self._pipeline = None

    def _get_external_checks(
        self, pipeline: Optional[GraphenePipelineSelector]
    ) -> Iterator[Tuple[CodeLocation, RemoteRepository, AssetCheckNodeSnap]]:
        if pipeline is None:
            entries = self._context.get_code_location_entries().values()
            for entry in entries:
                code_loc = entry.code_location
                if code_loc:
                    for repo in code_loc.get_repositories().values():
                        for check in repo.get_asset_check_node_snaps():
                            yield (code_loc, repo, check)

        else:
            job_name = cast(str, pipeline.pipelineName)
            repo_sel = RepositorySelector.from_graphql_input(pipeline)
            location = self._context.get_code_location(repo_sel.location_name)
            repo = location.get_repository(repo_sel.repository_name)
            asset_check_node_snaps = repo.get_asset_check_node_snaps(job_name=job_name)
            for snap in asset_check_node_snaps:
                yield (location, repo, snap)

    def _fetch_checks(
        self, limit_per_asset: Optional[int], pipeline: Optional[GraphenePipelineSelector]
    ) -> Mapping[AssetKey, AssetChecksOrErrorUnion]:
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

        external_checks_by_asset_key: Mapping[AssetKey, List[AssetCheckNodeSnap]] = {}
        errors: Mapping[AssetKey, GrapheneAssetCheckNeedsUserCodeUpgrade] = {}

        for location, _, external_check in self._get_external_checks(pipeline=pipeline):
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
                    external_checks_by_asset_key.setdefault(external_check.asset_key, []).append(
                        external_check
                    )

        if limit_per_asset:
            for asset_key, external_checks_for_asset in external_checks_by_asset_key.items():
                external_checks_by_asset_key[asset_key] = external_checks_for_asset[
                    :limit_per_asset
                ]

        # prefetch the checks and prepare the runs that will be needed to resolve their statuses
        # note: this would not be necessary if this was async
        all_check_keys = [
            external_check.key
            for external_checks in external_checks_by_asset_key.values()
            for external_check in external_checks
        ]
        check_records = AssetCheckExecutionRecord.blocking_get_many(self._context, all_check_keys)
        RunRecord.prepare(
            self._context,
            [
                r.run_id
                for r in check_records
                if r.status == AssetCheckExecutionRecordStatus.PLANNED
            ],
        )

        asset_graph = self._context.asset_graph
        graphene_checks: Mapping[AssetKey, AssetChecksOrErrorUnion] = {}
        for asset_key in self._asset_keys:
            if asset_key in errors:
                graphene_checks[asset_key] = errors[asset_key]
            else:
                graphene_checks_for_asset = []
                for external_check in external_checks_by_asset_key.get(asset_key, []):
                    can_execute_individually = (
                        GrapheneAssetCheckCanExecuteIndividually.CAN_EXECUTE
                        if len(
                            asset_graph.get_execution_set_asset_and_check_keys(external_check.key)
                        )
                        <= 1
                        # NOTE: once we support multi checks, we'll need to add a case for
                        # non subsettable multi checks
                        else GrapheneAssetCheckCanExecuteIndividually.REQUIRES_MATERIALIZATION
                    )
                    graphene_checks_for_asset.append(
                        GrapheneAssetCheck(
                            asset_check=external_check,
                            can_execute_individually=can_execute_individually,
                        )
                    )
                graphene_checks[asset_key] = GrapheneAssetChecks(checks=graphene_checks_for_asset)

        return graphene_checks

    def get_checks_for_asset(
        self,
        asset_key: AssetKey,
        limit: Optional[int] = None,
        pipeline: Optional[GraphenePipelineSelector] = None,
    ) -> AssetChecksOrErrorUnion:
        if self._checks is None:
            self._limit_per_asset = limit
            self._pipeline = pipeline
            self._checks = self._fetch_checks(limit_per_asset=limit, pipeline=pipeline)
        else:
            check.invariant(
                self._limit_per_asset == limit and self._pipeline == pipeline,
                "Limit and pipeline must be the same for all calls to this loader",
            )

        check.invariant(
            asset_key in self._checks, f"Asset key {asset_key} not included in this loader."
        )

        return self._checks[asset_key]
