"""Test job business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.api_layer.schemas.job import (
    DgApiJob,
    DgApiJobList,
    DgApiJobScheduleSummary,
    DgApiJobSensorSummary,
    DgApiJobTag,
)
from dagster_dg_cli.cli.api.formatters import format_job, format_jobs


class TestFormatJobs:
    """Test the job list formatting functions."""

    def _create_sample_job_list(self):
        """Create sample DgApiJobList for testing."""
        jobs = [
            DgApiJob(
                id="job-001",
                name="analytics_daily_job",
                description="Runs daily analytics pipeline",
                is_asset_job=True,
                tags=[DgApiJobTag(key="dagster/priority", value="high")],
                schedules=[
                    DgApiJobScheduleSummary(
                        name="analytics_daily_schedule",
                        cron_schedule="0 6 * * *",
                        status="RUNNING",
                    )
                ],
                sensors=[],
                repository_origin="dagster_open_platform@__repository__",
            ),
            DgApiJob(
                id="job-002",
                name="etl_ingestion_job",
                description="Ingests data from external sources",
                is_asset_job=False,
                tags=[],
                schedules=[],
                sensors=[DgApiJobSensorSummary(name="new_files_sensor", status="RUNNING")],
                repository_origin="dagster_open_platform@__repository__",
            ),
            DgApiJob(
                id="job-003",
                name="__ASSET_JOB_0",
                description=None,
                is_asset_job=True,
                tags=[],
                schedules=[],
                sensors=[],
                repository_origin="dagster_open_platform@__repository__",
            ),
        ]
        return DgApiJobList(items=jobs, total=3)

    def _create_empty_job_list(self):
        """Create empty DgApiJobList for testing."""
        return DgApiJobList(items=[], total=0)

    def test_format_jobs_text_output(self, snapshot):
        """Test formatting job list as text."""
        job_list = self._create_sample_job_list()
        result = format_jobs(job_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_jobs_json_output(self, snapshot):
        """Test formatting job list as JSON."""
        job_list = self._create_sample_job_list()
        result = format_jobs(job_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_jobs_text_output(self, snapshot):
        """Test formatting empty job list as text."""
        job_list = self._create_empty_job_list()
        result = format_jobs(job_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_empty_jobs_json_output(self, snapshot):
        """Test formatting empty job list as JSON."""
        job_list = self._create_empty_job_list()
        result = format_jobs(job_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestFormatJob:
    """Test the single job formatting functions."""

    def _create_full_job(self):
        """Create a job with all fields populated."""
        return DgApiJob(
            id="job-001",
            name="analytics_daily_job",
            description="Runs daily analytics pipeline",
            is_asset_job=True,
            tags=[
                DgApiJobTag(key="dagster/priority", value="high"),
                DgApiJobTag(key="team", value="data-platform"),
            ],
            schedules=[
                DgApiJobScheduleSummary(
                    name="analytics_daily_schedule",
                    cron_schedule="0 6 * * *",
                    status="RUNNING",
                )
            ],
            sensors=[DgApiJobSensorSummary(name="data_freshness_sensor", status="RUNNING")],
            repository_origin="dagster_open_platform@__repository__",
        )

    def _create_minimal_job(self):
        """Create a job with minimal fields."""
        return DgApiJob(
            id="job-002",
            name="simple_job",
            description=None,
            is_asset_job=False,
            tags=[],
            schedules=[],
            sensors=[],
        )

    def test_format_job_text_output(self, snapshot):
        """Test formatting single job as text."""
        job = self._create_full_job()
        result = format_job(job, as_json=False)
        snapshot.assert_match(result)

    def test_format_job_json_output(self, snapshot):
        """Test formatting single job as JSON."""
        job = self._create_full_job()
        result = format_job(job, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_minimal_job_text_output(self, snapshot):
        """Test formatting minimal job as text."""
        job = self._create_minimal_job()
        result = format_job(job, as_json=False)
        snapshot.assert_match(result)

    def test_format_minimal_job_json_output(self, snapshot):
        """Test formatting minimal job as JSON."""
        job = self._create_minimal_job()
        result = format_job(job, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


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
