from unittest.mock import patch

import dagster as dg
from dagster._core.storage.migrate import MigrateIOStorageResult
from docs_snippets.guides.migrations.migrate_io_storage import defs, migration_job


def test_migrate_io_storage_snippet_loads():
    """Verify the snippet's Definitions and job are properly defined."""
    assert isinstance(migration_job, dg.JobDefinition)
    assert isinstance(defs, dg.Definitions)


def test_migration_job_executes():
    """Execute the snippet's migration_job with migrate_io_storage mocked."""
    mock_result = MigrateIOStorageResult(migrated=(), skipped=(), failed=())

    with patch("dagster.migrate_io_storage", return_value=mock_result):
        result = migration_job.execute_in_process()

    assert result.success
