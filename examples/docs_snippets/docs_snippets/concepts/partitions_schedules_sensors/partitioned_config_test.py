"""isort:skip_file"""


from docs_snippets.concepts.partitions_schedules_sensors.partitioned_job import do_stuff_partitioned


# start
from dagster import validate_run_config, daily_partitioned_config
from datetime import datetime


@daily_partitioned_config(start_date=datetime(2020, 1, 1))
def my_partitioned_config(start: datetime, _end: datetime):
    return {"ops": {"process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}}}


def test_my_partitioned_config():
    # assert that the decorated function returns the expected output
    run_config = my_partitioned_config(datetime(2020, 1, 3), datetime(2020, 1, 4))
    assert run_config == {"ops": {"process_data_for_date": {"config": {"date": "2020-01-03"}}}}

    # assert that the output of the decorated function is valid configuration for the
    # do_stuff_partitioned job
    assert validate_run_config(do_stuff_partitioned, run_config)


# end
