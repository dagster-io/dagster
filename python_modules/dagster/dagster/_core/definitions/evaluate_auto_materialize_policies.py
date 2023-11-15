import logging
from typing import AbstractSet, NamedTuple, Optional, Sequence, Union

from dagster._annotations import experimental, public
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_graph import InternalAssetGraph
from dagster._core.definitions.assets import AssetsDefinition, SourceAsset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import RunRequest
from dagster._core.execution.api import ephemeral_instance_if_missing
from dagster._core.instance import DagsterInstance
from dagster._utils.warnings import disable_dagster_warnings


@experimental
class EvaluateAutoMaterializePoliciesResult(NamedTuple):
    """The result of invoking evaluate_auto_materialize_policies.

    Attributes:
        run_requests (Sequence[RunRequest]): The runs requested by the evaluation.
    """

    run_requests: Sequence[RunRequest]

    @public
    @property
    def requested_asset_keys(self) -> AbstractSet[AssetKey]:
        return {
            asset_key
            for run_request in self.run_requests
            for asset_key in run_request.asset_selection or []
        }


@experimental
def evaluate_auto_materialize_policies(
    *,
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    instance: Optional[DagsterInstance] = None,
    logger: Optional[logging.Logger] = None,
) -> EvaluateAutoMaterializePoliciesResult:
    """Evaluates the auto-materialize policies on the given assets.

    Args:
        assets (Sequence[Union[AssetsDefinition, SourceAsset]]): The assets to evaluate the
            auto-materialize policies on.
        instance (Optional[DagsterInstance]): The instance to evaluate against, an ephemeral one will
            be used if none is provided.
        logger (Optional[logging.Logger]): The logger to log to. logging.getLogger() will be used if
            none is provided.
    """
    from dagster._core.definitions.asset_daemon_context import AssetDaemonContext

    with ephemeral_instance_if_missing(instance) as instance:
        with disable_dagster_warnings():
            asset_graph = InternalAssetGraph.from_assets(assets)

            new_run_requests, new_cursor, new_evaluations = AssetDaemonContext(
                asset_graph=asset_graph,
                target_asset_keys=None,
                instance=instance,
                materialize_run_tags={},
                observe_run_tags={},
                cursor=AssetDaemonCursor.empty(),
                auto_observe=False,
                respect_materialization_data_versions=False,
                logger=logger or logging.getLogger(),
            ).evaluate()

            return EvaluateAutoMaterializePoliciesResult(new_run_requests)
