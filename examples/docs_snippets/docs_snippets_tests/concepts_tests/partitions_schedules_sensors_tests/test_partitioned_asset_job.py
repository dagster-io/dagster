from docs_snippets.concepts.partitions_schedules_sensors.partitioned_asset_job import (
    repo,
)


def test():
    assert repo.get_job("asset_1_and_2_job")
