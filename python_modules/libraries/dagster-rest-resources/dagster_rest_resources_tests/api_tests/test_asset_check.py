from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import (
    AssetCheckCanExecuteIndividually,
    AssetCheckExecutionResolvedStatus,
)
from dagster_rest_resources.__generated__.input_types import AssetKeyInput
from dagster_rest_resources.__generated__.list_asset_check_executions import (
    ListAssetCheckExecutions,
    ListAssetCheckExecutionsAssetCheckExecutions,
)
from dagster_rest_resources.__generated__.list_asset_checks import (
    ListAssetChecks,
    ListAssetChecksAssetNodeOrErrorAssetNode,
    ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetCheckNeedsAgentUpgradeError,
    ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetCheckNeedsMigrationError,
    ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetCheckNeedsUserCodeUpgrade,
    ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetChecks,
    ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetChecksChecks,
    ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetChecksChecksAssetKey,
    ListAssetChecksAssetNodeOrErrorAssetNotFoundError,
)
from dagster_rest_resources.api.asset_check import (
    DgApiAssetCheckApi,
    DgApiAssetCheckExecutionList,
    DgApiAssetCheckList,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError


def _make_check(
    name: str = "test-check",
    asset_key_path: list[str] | None = None,
    description: str | None = "test-description",
    blocking: bool = True,
    job_names: list[str] | None = None,
    can_execute_individually: AssetCheckCanExecuteIndividually = AssetCheckCanExecuteIndividually.CAN_EXECUTE,
) -> ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetChecksChecks:
    return ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetChecksChecks(
        name=name,
        assetKey=ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetChecksChecksAssetKey(
            path=asset_key_path or ["test", "path"]
        ),
        description=description,
        blocking=blocking,
        jobNames=job_names or ["test-job-name"],
        canExecuteIndividually=can_execute_individually,
    )


def _make_asset_node_result(
    checks: list[ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetChecksChecks],
) -> ListAssetChecks:
    return ListAssetChecks(
        assetNodeOrError=ListAssetChecksAssetNodeOrErrorAssetNode(
            __typename="AssetNode",
            assetChecksOrError=ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetChecks(
                __typename="AssetChecks",
                checks=checks,
            ),
        )
    )


class TestListAssetChecks:
    def test_returns_checks(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_checks.return_value = _make_asset_node_result(
            checks=[
                _make_check(name="check_a"),
                _make_check(name="check_b", asset_key_path=["other", "path"]),
            ]
        )
        result = DgApiAssetCheckApi(client).list_asset_checks("test/key")

        client.list_asset_checks.assert_called_once_with(
            asset_key=AssetKeyInput(path=["test", "key"])
        )
        assert len(result.items) == 2
        assert result.items[0].name == "check_a"
        assert result.items[1].name == "check_b"
        assert result.items[0].asset_key == "test/path"
        assert result.items[1].asset_key == "other/path"

    def test_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_checks.return_value = _make_asset_node_result(checks=[])
        result = DgApiAssetCheckApi(client).list_asset_checks("test/key")

        assert result == DgApiAssetCheckList(items=[])

    def test_asset_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_checks.return_value = ListAssetChecks(
            assetNodeOrError=ListAssetChecksAssetNodeOrErrorAssetNotFoundError(
                __typename="AssetNotFoundError",
                message="",
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Asset not found"):
            DgApiAssetCheckApi(client).list_asset_checks("missing/asset")

    def test_needs_migration_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_checks.return_value = ListAssetChecks(
            assetNodeOrError=ListAssetChecksAssetNodeOrErrorAssetNode(
                __typename="AssetNode",
                assetChecksOrError=ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetCheckNeedsMigrationError(
                    __typename="AssetCheckNeedsMigrationError",
                    message="",
                ),
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Asset check needs migration"):
            DgApiAssetCheckApi(client).list_asset_checks("test/key")

    def test_needs_user_code_upgrade_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_checks.return_value = ListAssetChecks(
            assetNodeOrError=ListAssetChecksAssetNodeOrErrorAssetNode(
                __typename="AssetNode",
                assetChecksOrError=ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetCheckNeedsUserCodeUpgrade(
                    __typename="AssetCheckNeedsUserCodeUpgrade",
                    message="",
                ),
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Asset check needs user code upgrade"):
            DgApiAssetCheckApi(client).list_asset_checks("test/key")

    def test_needs_agent_upgrade_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_checks.return_value = ListAssetChecks(
            assetNodeOrError=ListAssetChecksAssetNodeOrErrorAssetNode(
                __typename="AssetNode",
                assetChecksOrError=ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetCheckNeedsAgentUpgradeError(
                    __typename="AssetCheckNeedsAgentUpgradeError",
                    message="",
                ),
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Asset check needs agent update"):
            DgApiAssetCheckApi(client).list_asset_checks("test/key")


def _make_execution(
    id: str = "test-exec",
    run_id: str = "test-run",
    status: AssetCheckExecutionResolvedStatus = AssetCheckExecutionResolvedStatus.SUCCEEDED,
    timestamp: float = 1706745600.0,
    partition: str | None = None,
    step_key: str | None = "test_step_key",
) -> ListAssetCheckExecutionsAssetCheckExecutions:
    return ListAssetCheckExecutionsAssetCheckExecutions(
        id=id,
        runId=run_id,
        status=status,
        timestamp=timestamp,
        partition=partition,
        stepKey=step_key,
    )


class TestGetCheckExecutions:
    def test_returns_executions(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_check_executions.return_value = ListAssetCheckExecutions(
            assetCheckExecutions=[
                _make_execution(id="exec-h"),
                _make_execution(id="exec-i"),
            ]
        )
        result = DgApiAssetCheckApi(client).get_check_executions(
            asset_key="test/key",
            check_name="test_name",
            limit=10,
            cursor="exec-g",
        )

        client.list_asset_check_executions.assert_called_once_with(
            asset_key=AssetKeyInput(path=["test", "key"]),
            check_name="test_name",
            limit=10,
            cursor="exec-g",
        )
        assert len(result.items) == 2
        assert result.items[0].id == "exec-h"
        assert result.items[1].id == "exec-i"

    def test_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_check_executions.return_value = ListAssetCheckExecutions(
            assetCheckExecutions=[]
        )
        result = DgApiAssetCheckApi(client).get_check_executions(
            asset_key="test/key",
            check_name="freshness_check",
        )

        assert result == DgApiAssetCheckExecutionList(items=[])
