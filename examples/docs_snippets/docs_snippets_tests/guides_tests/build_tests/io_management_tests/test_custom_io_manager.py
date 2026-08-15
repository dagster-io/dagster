import dagster as dg
from docs_snippets.guides.build.io_management.custom_io_manager import (
    MetadataReadingIOManager,
    downstream_asset_with_definition_metadata,
    my_job,
    my_job_with_metadata,
    upstream_asset_with_definition_metadata,
)


def test_custom_io_manager():
    my_job.execute_in_process()


def test_custom_io_manager_with_metadata():
    my_job_with_metadata.execute_in_process()


def test_metadata_reading_io_manager():
    assert dg.materialize(
        [
            upstream_asset_with_definition_metadata,
            downstream_asset_with_definition_metadata,
        ],
        resources={"io_manager": MetadataReadingIOManager()},
    ).success
