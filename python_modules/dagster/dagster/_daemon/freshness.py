import asyncio
import os

import structlog

from dagster._core.definitions.assets.graph.remote_asset_graph import BaseAssetNode
from dagster._core.definitions.freshness import (
    FreshnessState,
    FreshnessStateChange,
    FreshnessStateRecord,
)
from dagster._core.definitions.freshness_evaluator import FRESHNESS_EVALUATORS_BY_POLICY_TYPE
from dagster._core.workspace.context import IWorkspaceProcessContext, LoadingContext
from dagster._daemon.daemon import IntervalDaemon
from dagster._time import get_current_timestamp

_INTERVAL_SECONDS = int(os.environ.get("FRESHNESS_DAEMON_INTERVAL_SECONDS", "30"))


class FreshnessDaemon(IntervalDaemon):
    def __init__(self, interval_seconds: int = _INTERVAL_SECONDS):
        super().__init__(interval_seconds=interval_seconds)

        self.logger = structlog.wrap_logger(
            self._logger,
        )

    @classmethod
    def daemon_type(cls):
        return "FRESHNESS_DAEMON"

    def run_iteration(self, workspace_process_context: IWorkspaceProcessContext):
        """On every daemon iteration, we try to evaluate freshness for all assets in the asset graph,
        skipping assets that do not have a freshness policy.
        """
        yield
        start_time = get_current_timestamp()
        self.logger.debug("Start freshness daemon iteration", start_timestamp=start_time)

        results = asyncio.run(
            self._evaluate_assets(workspace_process_context=workspace_process_context)
        )
        end_time = get_current_timestamp()

        self.logger.debug(
            f"End freshness daemon iteration.\n Evaluated: {len(results)}\nState Updated: {sum(results)}",
            start_timestamp=start_time,
            end_timestamp=end_time,
            daemon_iteration_seconds=end_time - start_time,
        )

    async def _evaluate_assets(
        self, workspace_process_context: IWorkspaceProcessContext
    ) -> list[bool]:
        """Evaluate the freshness state of all assets in the asset graph.

        Returns:
            A list of booleans indicating whether the freshness state changed for each asset.
        """
        # create a loading context to batch queries against
        loading_context = workspace_process_context.create_request_context()
        asset_graph = loading_context.asset_graph

        coroutines = [
            self._evaluate_asset(context=loading_context, node=node)
            for node in asset_graph.asset_nodes
        ]
        return await asyncio.gather(*coroutines)

    async def _compute_asset_freshness_state(
        self, context: LoadingContext, node: BaseAssetNode
    ) -> FreshnessState:
        """Given an asset spec, return the current freshness state of the asset."""
        # The freshness policy from 1.11 onwards is stored as a first-class property on the asset node.
        # Prior to 1.11, it was stored as a metadata field on the asset spec.
        # We need to support both cases.
        freshness_policy = node.freshness_policy_or_from_metadata
        if not freshness_policy:
            return FreshnessState.NOT_APPLICABLE

        evaluator = FRESHNESS_EVALUATORS_BY_POLICY_TYPE.get(freshness_policy.__class__)
        if not evaluator:
            self.logger.warning(
                f"Asset {node.key} has freshness policy type {freshness_policy.__class__} that has no freshness evaluator"
            )
            return FreshnessState.UNKNOWN

        return await evaluator().evaluate_freshness(context=context, node=node)

    async def _evaluate_asset(self, context: LoadingContext, node: BaseAssetNode) -> bool:
        """Computes the current freshness state of an asset and emits a freshness state change event if the state has changed.

        Returns:
            True if the freshness state has changed, False otherwise.
        """
        previous_state = await FreshnessStateRecord.gen(context, node.key)
        current_state = await self._compute_asset_freshness_state(context=context, node=node)
        if previous_state is None or previous_state.freshness_state != current_state:
            # Note: future refactors could batch the event emission given a new instance method, but freshness state change
            # events are somewhat rare so batching would not improve performance significantly
            context.instance._report_runless_asset_event(  # noqa: SLF001
                asset_event=FreshnessStateChange(
                    key=node.key,
                    previous_state=previous_state.freshness_state
                    if previous_state
                    else FreshnessState.UNKNOWN,
                    new_state=current_state,
                    state_change_timestamp=get_current_timestamp(),
                )
            )
            return True
        return False
