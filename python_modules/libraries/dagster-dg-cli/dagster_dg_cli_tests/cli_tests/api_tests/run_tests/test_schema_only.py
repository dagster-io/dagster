"""Test run schema models in isolation.

These tests verify the basic data models work correctly without
importing any CLI or GraphQL components that might have import issues.
"""

import json

from dagster_dg_cli.api_layer.schemas.run import DgApiRun, DgApiRunList, DgApiRunStatus


class TestRunSchema:
    """Test the Run schema model."""

    def test_run_creation_minimal(self):
        """Test creating run with minimal required fields."""
        run = DgApiRun(
            id="test-run-123",
            status=DgApiRunStatus.QUEUED,
            created_at=1705311000.0,  # 2024-01-15T10:30:00Z
        )

        assert run.id == "test-run-123"
        assert run.status == DgApiRunStatus.QUEUED
        assert run.created_at == 1705311000.0
        assert run.started_at is None
        assert run.ended_at is None
        assert run.job_name is None

    def test_run_creation_complete(self):
        """Test creating run with all fields."""
        run = DgApiRun(
            id="complete-run-456",
            status=DgApiRunStatus.SUCCESS,
            created_at=1705311000.0,  # 2024-01-15T10:30:00Z
            started_at=1705311060.0,  # 2024-01-15T10:31:00Z
            ended_at=1705311900.0,  # 2024-01-15T10:45:00Z
            job_name="my_pipeline",
        )

        assert run.id == "complete-run-456"
        assert run.status == DgApiRunStatus.SUCCESS
        assert run.created_at == 1705311000.0
        assert run.started_at == 1705311060.0
        assert run.ended_at == 1705311900.0
        assert run.job_name == "my_pipeline"

    def test_run_json_serialization(self):
        """Test that Run can be serialized to JSON."""
        run = DgApiRun(
            id="json-test-789",
            status=DgApiRunStatus.FAILURE,
            created_at=1705311000.0,  # 2024-01-15T10:30:00Z
            started_at=1705311060.0,  # 2024-01-15T10:31:00Z
            ended_at=1705311180.0,  # 2024-01-15T10:33:00Z
            job_name="failing_pipeline",
        )

        json_str = run.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["id"] == "json-test-789"
        assert parsed["status"] == "FAILURE"
        assert parsed["created_at"] == 1705311000.0
        assert parsed["started_at"] == 1705311060.0
        assert parsed["ended_at"] == 1705311180.0
        assert parsed["job_name"] == "failing_pipeline"

    def test_run_json_deserialization(self):
        """Test that Run can be created from JSON."""
        json_data = {
            "id": "from-json-abc",
            "status": "STARTED",
            "created_at": 1705311000.0,  # 2024-01-15T10:30:00Z
            "started_at": 1705311060.0,  # 2024-01-15T10:31:00Z
            "ended_at": None,
            "job_name": "json_pipeline",
        }

        run = DgApiRun(**json_data)

        assert run.id == "from-json-abc"
        assert run.status == DgApiRunStatus.STARTED
        assert run.created_at == 1705311000.0
        assert run.started_at == 1705311060.0
        assert run.ended_at is None
        assert run.job_name == "json_pipeline"


class TestRunStatusEnum:
    """Test the RunStatus enum."""

    def test_run_status_values(self):
        """Test that all expected RunStatus values are available."""
        expected_statuses = [
            "QUEUED",
            "STARTING",
            "STARTED",
            "SUCCESS",
            "FAILURE",
            "CANCELING",
            "CANCELED",
        ]

        actual_statuses = [status.value for status in DgApiRunStatus]
        assert set(actual_statuses) == set(expected_statuses)

    def test_run_status_enum_creation(self):
        """Test creating runs with each status value."""
        for status in DgApiRunStatus:
            run = DgApiRun(
                id=f"test-{status.value.lower()}",
                status=status,
                created_at=1705311000.0,  # 2024-01-15T10:30:00Z
            )
            assert run.status == status

    def test_run_status_string_values(self):
        """Test specific string values of statuses."""
        assert DgApiRunStatus.QUEUED.value == "QUEUED"
        assert DgApiRunStatus.STARTING.value == "STARTING"
        assert DgApiRunStatus.STARTED.value == "STARTED"
        assert DgApiRunStatus.SUCCESS.value == "SUCCESS"
        assert DgApiRunStatus.FAILURE.value == "FAILURE"
        assert DgApiRunStatus.CANCELING.value == "CANCELING"
        assert DgApiRunStatus.CANCELED.value == "CANCELED"


class TestRunListSchema:
    """Test the DgApiRunList schema model."""

    def test_run_list_creation(self):
        """Test creating run list with items."""
        runs = [
            DgApiRun(
                id="run-1",
                status=DgApiRunStatus.SUCCESS,
                created_at=1705311000.0,
                job_name="my_job",
            ),
            DgApiRun(
                id="run-2",
                status=DgApiRunStatus.FAILURE,
                created_at=1705312000.0,
                job_name="other_job",
            ),
        ]
        run_list = DgApiRunList(items=runs, total=2)

        assert len(run_list.items) == 2
        assert run_list.total == 2
        assert run_list.cursor is None
        assert run_list.has_more is False

    def test_run_list_with_pagination(self):
        """Test creating run list with pagination fields."""
        runs = [
            DgApiRun(
                id="run-1",
                status=DgApiRunStatus.SUCCESS,
                created_at=1705311000.0,
            ),
        ]
        run_list = DgApiRunList(
            items=runs,
            total=100,
            cursor="run-1",
            has_more=True,
        )

        assert run_list.total == 100
        assert run_list.cursor == "run-1"
        assert run_list.has_more is True

    def test_run_list_empty(self):
        """Test creating empty run list."""
        run_list = DgApiRunList(items=[], total=0)

        assert len(run_list.items) == 0
        assert run_list.total == 0
        assert run_list.has_more is False

    def test_run_list_json_serialization(self):
        """Test that DgApiRunList can be serialized to JSON."""
        runs = [
            DgApiRun(
                id="run-1",
                status=DgApiRunStatus.SUCCESS,
                created_at=1705311000.0,
                job_name="my_job",
            ),
        ]
        run_list = DgApiRunList(items=runs, total=1, cursor="run-1", has_more=False)

        json_str = run_list.model_dump_json()
        parsed = json.loads(json_str)

        assert len(parsed["items"]) == 1
        assert parsed["total"] == 1
        assert parsed["cursor"] == "run-1"
        assert parsed["has_more"] is False
        assert parsed["items"][0]["id"] == "run-1"
        assert parsed["items"][0]["status"] == "SUCCESS"
