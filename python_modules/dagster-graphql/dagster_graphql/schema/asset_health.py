import asyncio
from typing import Optional

import graphene
from dagster import _check as check
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.freshness import FreshnessState
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus
from dagster._core.storage.dagster_run import RunRecord
from dagster._core.storage.event_log.base import AssetCheckSummaryRecord, AssetRecord

from dagster_graphql.implementation.fetch_partition_subsets import (
    regenerate_and_check_partition_subsets,
)
from dagster_graphql.schema.util import ResolveInfo


class GrapheneAssetHealthStatus(graphene.Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"

    class Meta:
        name = "AssetHealthStatus"


class GrapheneAssetHealthCheckDegradedMeta(graphene.ObjectType):
    numFailedChecks = graphene.NonNull(graphene.Int)
    numWarningChecks = graphene.NonNull(graphene.Int)
    totalNumChecks = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthCheckDegradedMeta"


class GrapheneAssetHealthCheckWarningMeta(graphene.ObjectType):
    numWarningChecks = graphene.NonNull(graphene.Int)
    totalNumChecks = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthCheckWarningMeta"


class GrapheneAssetHealthCheckUnknownMeta(graphene.ObjectType):
    numNotExecutedChecks = graphene.NonNull(graphene.Int)
    totalNumChecks = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthCheckUnknownMeta"


class GrapheneAssetHealthCheckMeta(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetHealthCheckDegradedMeta,
            GrapheneAssetHealthCheckWarningMeta,
            GrapheneAssetHealthCheckUnknownMeta,
        )
        name = "AssetHealthCheckMeta"


class GrapheneAssetHealthMaterializationDegradedPartitionedMeta(graphene.ObjectType):
    numFailedPartitions = graphene.NonNull(graphene.Int)
    numMissingPartitions = graphene.NonNull(graphene.Int)
    totalNumPartitions = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthMaterializationDegradedPartitionedMeta"


class GrapheneAssetHealthMaterializationHealthyPartitionedMeta(graphene.ObjectType):
    numMissingPartitions = graphene.NonNull(graphene.Int)
    totalNumPartitions = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthMaterializationHealthyPartitionedMeta"


class GrapheneAssetHealthMaterializationDegradedNotPartitionedMeta(graphene.ObjectType):
    failedRunId = graphene.NonNull(graphene.String)

    class Meta:
        name = "AssetHealthMaterializationDegradedNotPartitionedMeta"


class GrapheneAssetHealthMaterializationMeta(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetHealthMaterializationDegradedPartitionedMeta,
            GrapheneAssetHealthMaterializationHealthyPartitionedMeta,
            GrapheneAssetHealthMaterializationDegradedNotPartitionedMeta,
        )
        name = "AssetHealthMaterializationMeta"


class GrapheneAssetHealthFreshnessMeta(graphene.ObjectType):
    lastMaterializedTimestamp = graphene.Field(graphene.Float)

    class Meta:
        name = "AssetHealthFreshnessMeta"


class GrapheneAssetHealth(graphene.ObjectType):
    assetHealth = graphene.NonNull(GrapheneAssetHealthStatus)
    materializationStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    materializationStatusMetadata = graphene.Field(GrapheneAssetHealthMaterializationMeta)
    assetChecksStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    assetChecksStatusMetadata = graphene.Field(GrapheneAssetHealthCheckMeta)
    freshnessStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    freshnessStatusMetadata = graphene.Field(GrapheneAssetHealthFreshnessMeta)

    class Meta:
        name = "AssetHealth"

    def __init__(self, asset_node_snap, dynamic_partitions_loader):
        super().__init__()
        self._asset_node_snap = asset_node_snap
        self._dynamic_partitions_loader = dynamic_partitions_loader
        self.materialization_status_task = None
        self.asset_check_status_task = None
        self.freshness_status_task = None

    async def get_materialization_status_for_asset_health(
        self, graphene_info: ResolveInfo
    ) -> tuple[str, Optional[GrapheneAssetHealthMaterializationMeta]]:
        """Computes the health indicator for the asset materialization status. Follows these rules:
        If the asset is partitioned:
            - HEALTHY - all partitions successfully materialized.
            - WARNING - some partitions are successful but any number of partitions are missing (but no failed partitions).
            - DEGRADED - any number of partitions are failed.
            - UNKNOWN - all partitions are missing.
        If the asset is not partitioned:
            - HEALTHY - the latest materialization of an asset was successfully materialized.
            - WARNING - no conditions lead to a warning status.
            - DEGRADED - latest materialization of an asset failed.
            - UNKNOWN - asset has never had a materialization attempt.
        """
        partitions_snap = self._asset_node_snap.partitions
        asset_key = self._asset_node_snap.asset_key
        if partitions_snap is not None:  # isPartitioned
            (
                materialized_partition_subset,
                failed_partition_subset,
                _,
            ) = regenerate_and_check_partition_subsets(
                graphene_info.context, self._asset_node_snap, self._dynamic_partitions_loader
            )
            total_num_partitions = partitions_snap.get_partitions_definition().get_num_partitions(
                dynamic_partitions_store=self._dynamic_partitions_loader
            )
            currently_materialized_subset = materialized_partition_subset - failed_partition_subset
            num_materialized = len(currently_materialized_subset)
            num_failed = len(failed_partition_subset)
            if num_materialized == 0 and num_failed == 0:
                # asset has never been materialized
                return GrapheneAssetHealthStatus.UNKNOWN, None
            num_missing = total_num_partitions - num_materialized - num_failed
            if num_failed > 0:
                return (
                    GrapheneAssetHealthStatus.DEGRADED,
                    GrapheneAssetHealthMaterializationDegradedPartitionedMeta(
                        numFailedPartitions=num_failed,
                        numMissingPartitions=num_missing,
                        totalNumPartitions=total_num_partitions,
                    ),
                )
            # missing partitions are ok as long as some partitions are successfully materialized (and no failures)
            # but we want to show the number of missing partitions in the metadata
            return (
                GrapheneAssetHealthStatus.HEALTHY,
                GrapheneAssetHealthMaterializationHealthyPartitionedMeta(
                    numMissingPartitions=num_missing,
                    totalNumPartitions=total_num_partitions,
                )
                if num_missing > 0
                else None,
            )

        asset_record = await AssetRecord.gen(graphene_info.context, asset_key)
        if asset_record is None:
            return GrapheneAssetHealthStatus.UNKNOWN, None
        asset_entry = asset_record.asset_entry

        if self._asset_node_snap.is_observable and not self._asset_node_snap.is_materializable:
            # for observable assets, if there is an observation event then the asset is healthy
            if asset_entry.last_observation is not None:
                return GrapheneAssetHealthStatus.HEALTHY, None
            else:
                return GrapheneAssetHealthStatus.UNKNOWN, None

        if graphene_info.context.instance.can_read_failure_events_for_asset(asset_record):
            # compute the status based on the asset key table
            if (
                asset_entry.last_materialization_storage_id is None
                and asset_entry.last_failed_to_materialize_storage_id is None
            ):
                # never materialized
                return GrapheneAssetHealthStatus.UNKNOWN, None
            if asset_entry.last_failed_to_materialize_storage_id is None:
                # last_materialization_record must be non-null, therefore the asset successfully materialized
                return GrapheneAssetHealthStatus.HEALTHY, None
            elif asset_entry.last_materialization_storage_id is None:
                # last_failed_to_materialize_record must be non-null, therefore the asset failed to materialize
                last_failed_record = check.not_none(asset_entry.last_failed_to_materialize_record)
                return (
                    GrapheneAssetHealthStatus.DEGRADED,
                    GrapheneAssetHealthMaterializationDegradedNotPartitionedMeta(
                        failedRunId=last_failed_record.run_id,
                    ),
                )

            if (
                asset_entry.last_materialization_storage_id
                > asset_entry.last_failed_to_materialize_storage_id
            ):
                # latest materialization succeeded
                return GrapheneAssetHealthStatus.HEALTHY, None
            # latest materialization failed
            last_failed_record = check.not_none(asset_entry.last_failed_to_materialize_record)
            return (
                GrapheneAssetHealthStatus.DEGRADED,
                GrapheneAssetHealthMaterializationDegradedNotPartitionedMeta(
                    failedRunId=last_failed_record.run_id,
                ),
            )
        # we are not storing failure events for this asset, so must compute status based on the information we have available
        # in some cases this results in reporting as asset as HEALTHY or UNKNOWN during an in progress run
        # even if the asset was previously failed
        else:
            # if the asset has been successfully materialized in the past, we fallback to that status
            # when we don't have the information available to compute status based on the latest run
            fallback_status_and_meta = (
                (GrapheneAssetHealthStatus.UNKNOWN, None)
                if asset_entry.last_materialization is None
                else (GrapheneAssetHealthStatus.HEALTHY, None)
            )
            if asset_entry.last_run_id is None:
                return fallback_status_and_meta

            assert asset_entry.last_run_id is not None
            if (
                asset_entry.last_materialization is not None
                and asset_entry.last_run_id == asset_entry.last_materialization.run_id
            ):
                # latest materialization succeeded in the latest run
                return GrapheneAssetHealthStatus.HEALTHY, None
            run_record = await RunRecord.gen(graphene_info.context, asset_entry.last_run_id)
            if run_record is None or not run_record.dagster_run.is_finished:
                return fallback_status_and_meta
            run_end_time = check.not_none(run_record.end_time)
            if (
                asset_entry.last_materialization
                and asset_entry.last_materialization.timestamp > run_end_time
            ):
                # latest materialization was reported manually
                return GrapheneAssetHealthStatus.HEALTHY, None
            if run_record.dagster_run.is_failure:
                return (
                    GrapheneAssetHealthStatus.DEGRADED,
                    GrapheneAssetHealthMaterializationDegradedNotPartitionedMeta(
                        failedRunId=run_record.dagster_run.run_id,
                    ),
                )

            return fallback_status_and_meta

    async def resolve_materializationStatus(self, graphene_info: ResolveInfo):
        if self.materialization_status_task is None:
            self.materialization_status_task = asyncio.create_task(
                self.get_materialization_status_for_asset_health(graphene_info)
            )
        materialization_status, _ = await self.materialization_status_task
        return materialization_status

    async def resolve_materializationStatusMetadata(self, graphene_info: ResolveInfo):
        if self.materialization_status_task is None:
            self.materialization_status_task = asyncio.create_task(
                self.get_materialization_status_for_asset_health(graphene_info)
            )
        _, materialization_status_metadata = await self.materialization_status_task
        return materialization_status_metadata

    async def get_asset_check_status_for_asset_health(
        self, graphene_info: ResolveInfo
    ) -> tuple[str, Optional[GrapheneAssetHealthCheckMeta]]:
        """Computes the health indicator for the asset checks for the assets. Follows these rules:
        HEALTHY - the latest completed execution for every check is a success.
        WARNING - the latest completed execution for any asset check failed with severity WARN
            (and no checks failed with severity ERROR).
        DEGRADED - the latest completed execution for any asset check failed with severity ERROR.
        UNKNOWN - any asset checks has never been executed.
        NOT_APPLICABLE - the asset has no asset checks defined.

        Note: the latest completed execution for each check may not have executed based on the
        most recent materialization of the asset.
        """
        remote_check_nodes = graphene_info.context.asset_graph.get_checks_for_asset(
            self._asset_node_snap.asset_key
        )
        if not remote_check_nodes or len(remote_check_nodes) == 0:
            # asset doesn't have checks defined
            return GrapheneAssetHealthStatus.NOT_APPLICABLE, None
        else:
            total_num_checks = len(remote_check_nodes)
            check_statuses = []
            check_failure_severities = []
            asset_check_summary_records = await AssetCheckSummaryRecord.gen_many(
                graphene_info.context,
                [remote_check_node.asset_check.key for remote_check_node in remote_check_nodes],
            )
            for summary_record in asset_check_summary_records:
                if summary_record is None or summary_record.last_check_execution_record is None:
                    # the check has never been executed.
                    continue

                # if the last_check_execution_record is completed, it will be the same as last_completed_check_execution_record,
                # but we check the last_check_execution_record status first since there is an edge case
                # where the record will have status PLANNED, but the resolve_status will be EXECUTION_FAILED
                # because the run for the check failed.
                last_check_execution_status = (
                    await summary_record.last_check_execution_record.resolve_status(
                        graphene_info.context
                    )
                )
                last_check_evaluation = summary_record.last_check_execution_record.evaluation

                if last_check_execution_status in [
                    AssetCheckExecutionResolvedStatus.IN_PROGRESS,
                    AssetCheckExecutionResolvedStatus.SKIPPED,
                ]:
                    # the last check is still in progress or is skipped, so we want to check the status of
                    # the latest completed check instead
                    if summary_record.last_completed_check_execution_record is None:
                        # the check hasn't been executed prior to this in progress check
                        continue
                    last_check_execution_status = (
                        await summary_record.last_completed_check_execution_record.resolve_status(
                            graphene_info.context
                        )
                    )
                    last_check_evaluation = (
                        summary_record.last_completed_check_execution_record.evaluation
                    )

                check_statuses.append(last_check_execution_status)
                if last_check_execution_status == AssetCheckExecutionResolvedStatus.FAILED:
                    # failed checks should always have an evaluation, but default to ERROR if not
                    check_failure_severities.append(
                        last_check_evaluation.severity
                        if last_check_evaluation
                        else AssetCheckSeverity.ERROR
                    )
                if (
                    last_check_execution_status
                    == AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
                ):
                    # EXECUTION_FAILED checks may not have an evaluation, and we want to show these as
                    # degraded health anyway.
                    check_failure_severities.append(AssetCheckSeverity.ERROR)

            num_unexecuted_checks = total_num_checks - len(check_statuses)

            if len(check_statuses) == 0:
                # checks have never been executed
                return GrapheneAssetHealthStatus.UNKNOWN, GrapheneAssetHealthCheckUnknownMeta(
                    numNotExecutedChecks=num_unexecuted_checks,
                    totalNumChecks=total_num_checks,
                )

            if any(
                status == AssetCheckExecutionResolvedStatus.FAILED
                or status == AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
                for status in check_statuses
            ):
                if all(
                    severity == AssetCheckSeverity.WARN for severity in check_failure_severities
                ):
                    # all failed checks are with warning severity
                    return (
                        GrapheneAssetHealthStatus.WARNING,
                        GrapheneAssetHealthCheckWarningMeta(
                            numWarningChecks=len(check_failure_severities),
                            totalNumChecks=total_num_checks,
                        ),
                    )
                # at least one failing check had error severity
                num_failed = len(
                    [sev for sev in check_failure_severities if sev == AssetCheckSeverity.ERROR]
                )
                num_warn = len(check_failure_severities) - num_failed
                return GrapheneAssetHealthStatus.DEGRADED, GrapheneAssetHealthCheckDegradedMeta(
                    numFailedChecks=num_failed,
                    numWarningChecks=num_warn,
                    totalNumChecks=total_num_checks,
                )

            # since we are only looking at the latest completed execution for each check, if there
            # are no failed checks, then all checks must have succeeded
            if num_unexecuted_checks > 0:
                # if any check has never been executed, we report this as unknown, even if other checks
                # have passed
                return (
                    GrapheneAssetHealthStatus.UNKNOWN,
                    GrapheneAssetHealthCheckUnknownMeta(
                        numNotExecutedChecks=num_unexecuted_checks,
                        totalNumChecks=total_num_checks,
                    ),
                )
            # all checks must have executed and passed
            return GrapheneAssetHealthStatus.HEALTHY, None

    async def resolve_assetChecksStatus(self, graphene_info: ResolveInfo):
        if self.asset_check_status_task is None:
            self.asset_check_status_task = asyncio.create_task(
                self.get_asset_check_status_for_asset_health(graphene_info)
            )

        asset_checks_status, _ = await self.asset_check_status_task
        return asset_checks_status

    async def resolve_assetChecksStatusMetadata(self, graphene_info: ResolveInfo):
        if self.asset_check_status_task is None:
            self.asset_check_status_task = asyncio.create_task(
                self.get_asset_check_status_for_asset_health(graphene_info)
            )

        _, asset_checks_status_metadata = await self.asset_check_status_task
        return asset_checks_status_metadata

    async def get_freshness_status_for_asset_health(
        self, graphene_info: ResolveInfo
    ) -> tuple[str, Optional[GrapheneAssetHealthFreshnessMeta]]:
        """Computes the health indicator for the freshness for an asset. Follows these rules:
        HEALTHY - the freshness policy is in a PASS-ing state
        WARNING - the freshness policy is in a WARN-ing state
        DEGRADED - the freshness policy is in a FAIL-ing state
        UNKNOWN - the freshness policy has never been evaluated or is in an UNKNOWN state
        NOT_APPLICABLE - the asset does not have a freshness policy defined.
        """
        if self._asset_node_snap.internal_freshness_policy is None:
            return GrapheneAssetHealthStatus.NOT_APPLICABLE, None

        freshness_state_record = graphene_info.context.instance.get_entity_freshness_state(
            self._asset_node_snap.asset_key
        )
        if freshness_state_record is None:
            return GrapheneAssetHealthStatus.UNKNOWN, None
        state = freshness_state_record.freshness_state
        if state == FreshnessState.PASS:
            return GrapheneAssetHealthStatus.HEALTHY, None

        asset_record = await AssetRecord.gen(graphene_info.context, self._asset_node_snap.asset_key)
        last_materialization = (
            asset_record.asset_entry.last_materialization.timestamp
            if asset_record and asset_record.asset_entry.last_materialization
            else None
        )
        if state == FreshnessState.WARN:
            return GrapheneAssetHealthStatus.WARNING, GrapheneAssetHealthFreshnessMeta(
                lastMaterializedTimestamp=last_materialization,
            )
        if state == FreshnessState.FAIL:
            return GrapheneAssetHealthStatus.DEGRADED, GrapheneAssetHealthFreshnessMeta(
                lastMaterializedTimestamp=last_materialization,
            )

        return GrapheneAssetHealthStatus.UNKNOWN, None

    async def resolve_freshnessStatus(self, graphene_info: ResolveInfo):
        if self.freshness_status_task is None:
            self.freshness_status_task = asyncio.create_task(
                self.get_freshness_status_for_asset_health(graphene_info)
            )

        freshness_status, _ = await self.freshness_status_task
        return freshness_status

    async def resolve_freshnessStatusMetadata(self, graphene_info: ResolveInfo):
        if self.freshness_status_task is None:
            self.freshness_status_task = asyncio.create_task(
                self.get_freshness_status_for_asset_health(graphene_info)
            )

        _, freshness_status_metadata = await self.freshness_status_task
        return freshness_status_metadata

    async def resolve_assetHealth(self, graphene_info: ResolveInfo):
        if not graphene_info.context.instance.dagster_observe_supported():
            return GrapheneAssetHealthStatus.UNKNOWN
        if self.materialization_status_task is None:
            self.materialization_status_task = asyncio.create_task(
                self.get_materialization_status_for_asset_health(graphene_info)
            )
        materialization_status, _ = await self.materialization_status_task
        if self.asset_check_status_task is None:
            self.asset_check_status_task = asyncio.create_task(
                self.get_asset_check_status_for_asset_health(graphene_info)
            )
        asset_checks_status, _ = await self.asset_check_status_task
        if self.freshness_status_task is None:
            self.freshness_status_task = asyncio.create_task(
                self.get_freshness_status_for_asset_health(graphene_info)
            )
        freshness_status, _ = await self.freshness_status_task
        statuses = [
            materialization_status,
            asset_checks_status,
            freshness_status,
        ]
        if GrapheneAssetHealthStatus.DEGRADED in statuses:
            return GrapheneAssetHealthStatus.DEGRADED
        if GrapheneAssetHealthStatus.WARNING in statuses:
            return GrapheneAssetHealthStatus.WARNING
        # at this point, all statuses are HEALTHY, UNKNOWN, or NOT_APPLICABLE
        if materialization_status == GrapheneAssetHealthStatus.UNKNOWN:
            return GrapheneAssetHealthStatus.UNKNOWN
        if all(
            status == GrapheneAssetHealthStatus.UNKNOWN
            or status == GrapheneAssetHealthStatus.NOT_APPLICABLE
            for status in statuses
        ):
            return GrapheneAssetHealthStatus.UNKNOWN
        # at least one status must be HEALTHY
        return GrapheneAssetHealthStatus.HEALTHY
