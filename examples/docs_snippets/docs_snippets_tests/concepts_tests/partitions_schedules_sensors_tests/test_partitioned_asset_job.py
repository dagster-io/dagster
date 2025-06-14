from docs_snippets.concepts.partitions_schedules_sensors.partitioned_asset_job import (
    defs,
)


def test_partitioned_asset_job() -> None:
    assert defs.resolve_job_def("asset_1_and_2_job")
