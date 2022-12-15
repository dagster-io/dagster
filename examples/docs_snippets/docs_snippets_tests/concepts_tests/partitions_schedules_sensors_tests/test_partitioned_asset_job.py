from docs_snippets.concepts.partitions_schedules_sensors.partitioned_asset_job import (
    defs,
)


def test():
    assert defs.get_job_def("asset_1_and_2_job")
