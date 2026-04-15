"""Test job business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_rest_resources.schemas.job import (
    DgApiJob,
    DgApiJobList,
    DgApiJobScheduleSummary,
    DgApiJobSensorSummary,
    DgApiJobTag,
)


class TestJobDataProcessing:
    """Test processing of job data structures."""

    def test_job_creation_with_all_fields(self):
        """Test creating a job with all fields."""
        job = DgApiJob(
            id="test-job",
            name="test_job",
            description="Test job",
            is_asset_job=True,
            tags=[DgApiJobTag(key="k", value="v")],
            schedules=[
                DgApiJobScheduleSummary(name="sched", cron_schedule="* * * * *", status="RUNNING")
            ],
            sensors=[DgApiJobSensorSummary(name="sensor", status="STOPPED")],
            repository_origin="loc@repo",
        )
        assert job.name == "test_job"
        assert job.is_asset_job is True
        assert len(job.tags) == 1
        assert len(job.schedules) == 1
        assert len(job.sensors) == 1

    def test_job_list_serialization(self, snapshot):
        """Test JSON serialization of job list."""
        job_list = DgApiJobList(
            items=[
                DgApiJob(
                    id="job-a",
                    name="job_a",
                    description="First job",
                    is_asset_job=True,
                ),
                DgApiJob(
                    id="job-b",
                    name="job_b",
                    description=None,
                    is_asset_job=False,
                ),
            ],
            total=2,
        )
        result = job_list.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)
