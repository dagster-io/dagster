from dataclasses import dataclass

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.input_types import AssetKeyInput
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.asset_check import (
    DgApiAssetCheck,
    DgApiAssetCheckExecution,
    DgApiAssetCheckExecutionList,
    DgApiAssetCheckList,
)
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError


@dataclass(frozen=True)
class DgApiAssetCheckApi:
    _client: IGraphQLClient

    def list_asset_checks(self, asset_key: str) -> DgApiAssetCheckList:
        node_result = self._client.list_asset_checks(
            asset_key=AssetKeyInput(path=asset_key.split("/"))
        ).asset_node_or_error

        match node_result.typename__:
            case "AssetNode":
                checks_result = node_result.asset_checks_or_error  # ty: ignore[unresolved-attribute]
                match checks_result.typename__:
                    case "AssetChecks":
                        return DgApiAssetCheckList(
                            items=[
                                DgApiAssetCheck(
                                    name=c.name,
                                    asset_key="/".join(c.asset_key.path),
                                    description=c.description,
                                    blocking=c.blocking,
                                    job_names=list(c.job_names),
                                    can_execute_individually=c.can_execute_individually,
                                )
                                for c in checks_result.checks  # ty: ignore[unresolved-attribute]
                            ]
                        )
                    case "AssetCheckNeedsMigrationError":
                        raise DagsterPlusGraphqlError(
                            f"Asset check needs migration: {checks_result.message}"  # ty: ignore[unresolved-attribute]
                        )
                    case "AssetCheckNeedsUserCodeUpgrade":
                        raise DagsterPlusGraphqlError(
                            f"Asset check needs user code upgrade: {checks_result.message}"  # ty: ignore[unresolved-attribute]
                        )
                    case "AssetCheckNeedsAgentUpgradeError":
                        raise DagsterPlusGraphqlError(
                            f"Asset check needs agent update: {checks_result.message}"  # ty: ignore[unresolved-attribute]
                        )
                    case _ as unreachable:
                        assert_never(unreachable)
            case "AssetNotFoundError":
                raise DagsterPlusGraphqlError(f"Asset not found: {node_result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_check_executions(
        self,
        *,
        asset_key: str,
        check_name: str,
        limit: int = 25,
        cursor: str | None = None,
    ) -> DgApiAssetCheckExecutionList:
        executions = self._client.list_asset_check_executions(
            asset_key=AssetKeyInput(path=asset_key.split("/")),
            check_name=check_name,
            limit=limit,
            cursor=cursor,
        ).asset_check_executions

        return DgApiAssetCheckExecutionList(
            items=[
                DgApiAssetCheckExecution(
                    id=e.id,
                    run_id=e.run_id,
                    status=e.status,
                    timestamp=e.timestamp,
                    partition=e.partition,
                    step_key=e.step_key,
                    check_name=check_name,
                    asset_key=asset_key,
                )
                for e in executions
            ]
        )
