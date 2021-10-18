"""isort:skip_file"""


from docs_snippets_crag.concepts.partitions_schedules_sensors.partitioned_job import (
    do_stuff_partitioned,
    my_partitioned_config,
)


# start
from dagster import validate_run_config


def test_my_partitioned_config():
    first_partition_key = my_partitioned_config.get_partition_keys()[0]
    run_config = my_partitioned_config.get_run_config(first_partition_key)
    assert run_config == {"ops": {"process_data_for_date": {"config": {"date": "2020-01-01"}}}}
    assert validate_run_config(do_stuff_partitioned, run_config)


# end
