import dagster as dg
from ingestion_patterns.definitions import defs


def test_definitions_can_load():
    """Test that the Definitions object loads without errors."""
    assert isinstance(defs, dg.Definitions)


def test_assets_exist():
    """Test that expected assets are defined."""
    repo = defs.get_repository_def()
    asset_graph = repo.asset_graph
    asset_keys = {key.to_user_string() for key in asset_graph.materializable_asset_keys}

    expected_assets = [
        "extract_source_data",
        "load_to_storage",
        "poll_kafka_events",
        "process_kafka_events",
        "process_webhook_data",
    ]

    for asset in expected_assets:
        assert asset in asset_keys, f"Asset '{asset}' not found in definitions"


def test_jobs_exist():
    """Test that expected jobs are defined."""
    repo = defs.get_repository_def()
    job_names = {job.name for job in repo.get_all_jobs()}

    expected_jobs = ["daily_pull_job", "kafka_poll_job", "webhook_processing_job"]

    for job in expected_jobs:
        assert job in job_names, f"Job '{job}' not found in definitions"


def test_sensors_exist():
    """Test that expected sensors are defined."""
    repo = defs.get_repository_def()
    sensor_names = {sensor.name for sensor in repo.sensor_defs}

    expected_sensors = ["kafka_polling_sensor", "webhook_pending_sensor"]

    for sensor in expected_sensors:
        assert sensor in sensor_names, f"Sensor '{sensor}' not found in definitions"


def test_schedules_exist():
    """Test that expected schedules are defined."""
    repo = defs.get_repository_def()
    schedule_names = {schedule.name for schedule in repo.schedule_defs}

    expected_schedules = ["daily_pull_schedule"]

    for schedule in expected_schedules:
        assert schedule in schedule_names, f"Schedule '{schedule}' not found in definitions"


def test_resources_exist():
    """Test that expected resources are defined."""
    repo = defs.get_repository_def()
    resource_keys = set(repo.get_top_level_resources().keys())

    assert "duckdb" in resource_keys, "DuckDB resource not found in definitions"
