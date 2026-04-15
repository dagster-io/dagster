"""Test asset check business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_rest_resources.schemas.asset_check import (
    DgApiAssetCheck,
    DgApiAssetCheckExecution,
    DgApiAssetCheckExecutionList,
    DgApiAssetCheckExecutionStatus,
    DgApiAssetCheckList,
)


class TestAssetCheckDataProcessing:
    """Test processing of asset check data structures."""

    def test_asset_check_creation(self):
        """Test creating an asset check with all fields."""
        check = DgApiAssetCheck(
            name="my_check",
            asset_key="my/asset",
            description="Test check",
            blocking=True,
            job_names=["job_1", "job_2"],
            can_execute_individually="CAN_EXECUTE",
        )
        assert check.name == "my_check"
        assert check.blocking is True
        assert len(check.job_names) == 2

    def test_asset_check_execution_all_statuses(self, snapshot):
        """Test creating executions with all possible status values."""
        executions = [
            DgApiAssetCheckExecution(
                id=f"exec-{status.value.lower()}",
                run_id=f"run-{status.value.lower()}",
                status=status,
                timestamp=1706745600.0,
                step_key="test_step",
                check_name="test_check",
                asset_key="my/asset",
            )
            for status in DgApiAssetCheckExecutionStatus
        ]

        execution_list = DgApiAssetCheckExecutionList(items=executions)
        result = execution_list.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_asset_check_list_serialization(self, snapshot):
        """Test JSON serialization of asset check list."""
        check_list = DgApiAssetCheckList(
            items=[
                DgApiAssetCheck(
                    name="check_a",
                    asset_key="my/asset",
                    description="First check",
                    blocking=True,
                ),
                DgApiAssetCheck(
                    name="check_b",
                    asset_key="my/asset",
                    description=None,
                    blocking=False,
                ),
            ]
        )
        result = check_list.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)
