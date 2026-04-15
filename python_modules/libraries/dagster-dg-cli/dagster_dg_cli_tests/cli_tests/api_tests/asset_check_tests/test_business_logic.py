"""Test asset check business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.cli.api.formatters import format_asset_check_executions, format_asset_checks
from dagster_rest_resources.schemas.asset_check import (
    DgApiAssetCheck,
    DgApiAssetCheckExecution,
    DgApiAssetCheckExecutionList,
    DgApiAssetCheckExecutionStatus,
    DgApiAssetCheckList,
)


class TestFormatAssetChecks:
    """Test the asset check formatting functions."""

    def _create_sample_check_list(self):
        """Create sample DgApiAssetCheckList for testing."""
        checks = [
            DgApiAssetCheck(
                name="freshness_check",
                asset_key="my/asset",
                description="Checks that the asset is materialized within the last 24 hours",
                blocking=True,
                job_names=["__ASSET_JOB_0"],
                can_execute_individually="CAN_EXECUTE",
            ),
            DgApiAssetCheck(
                name="row_count_check",
                asset_key="my/asset",
                description="Validates minimum row count",
                blocking=False,
                job_names=["__ASSET_JOB_0"],
                can_execute_individually="CAN_EXECUTE",
            ),
            DgApiAssetCheck(
                name="schema_check",
                asset_key="my/asset",
                description=None,
                blocking=False,
                job_names=[],
                can_execute_individually="REQUIRES_MATERIALIZATION",
            ),
        ]
        return DgApiAssetCheckList(items=checks)

    def _create_empty_check_list(self):
        """Create empty DgApiAssetCheckList for testing."""
        return DgApiAssetCheckList(items=[])

    def test_format_asset_checks_text_output(self, snapshot):
        """Test formatting asset checks as text."""
        check_list = self._create_sample_check_list()
        result = format_asset_checks(check_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_asset_checks_json_output(self, snapshot):
        """Test formatting asset checks as JSON."""
        check_list = self._create_sample_check_list()
        result = format_asset_checks(check_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_asset_checks_text_output(self, snapshot):
        """Test formatting empty asset check list as text."""
        check_list = self._create_empty_check_list()
        result = format_asset_checks(check_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_empty_asset_checks_json_output(self, snapshot):
        """Test formatting empty asset check list as JSON."""
        check_list = self._create_empty_check_list()
        result = format_asset_checks(check_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestFormatAssetCheckExecutions:
    """Test the asset check execution formatting functions."""

    def _create_sample_executions(self):
        """Create sample DgApiAssetCheckExecutionList for testing."""
        executions = [
            DgApiAssetCheckExecution(
                id="exec-001",
                run_id="run-abc-123",
                status=DgApiAssetCheckExecutionStatus.SUCCEEDED,
                timestamp=1706745600.0,  # 2024-01-31T16:00:00 UTC
                step_key="my_asset_freshness_check",
                check_name="freshness_check",
                asset_key="my/asset",
            ),
            DgApiAssetCheckExecution(
                id="exec-002",
                run_id="run-def-456",
                status=DgApiAssetCheckExecutionStatus.FAILED,
                timestamp=1706659200.0,  # 2024-01-30T16:00:00 UTC
                step_key="my_asset_freshness_check",
                check_name="freshness_check",
                asset_key="my/asset",
            ),
            DgApiAssetCheckExecution(
                id="exec-003",
                run_id="run-ghi-789",
                status=DgApiAssetCheckExecutionStatus.IN_PROGRESS,
                timestamp=1706572800.0,  # 2024-01-29T16:00:00 UTC
                step_key="my_asset_freshness_check",
                check_name="freshness_check",
                asset_key="my/asset",
                partition="2024-01-29",
            ),
        ]
        return DgApiAssetCheckExecutionList(items=executions)

    def _create_empty_executions(self):
        """Create empty DgApiAssetCheckExecutionList for testing."""
        return DgApiAssetCheckExecutionList(items=[])

    def test_format_asset_check_executions_text_output(self, snapshot):
        """Test formatting asset check executions as text."""
        from dagster_shared.utils.timing import fixed_timezone

        execution_list = self._create_sample_executions()
        with fixed_timezone("UTC"):
            result = format_asset_check_executions(execution_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_asset_check_executions_json_output(self, snapshot):
        """Test formatting asset check executions as JSON."""
        execution_list = self._create_sample_executions()
        result = format_asset_check_executions(execution_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_executions_text_output(self, snapshot):
        """Test formatting empty execution list as text."""
        execution_list = self._create_empty_executions()
        result = format_asset_check_executions(execution_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_empty_executions_json_output(self, snapshot):
        """Test formatting empty execution list as JSON."""
        execution_list = self._create_empty_executions()
        result = format_asset_check_executions(execution_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)
