from dagster_cron import SystemCronScheduler
from dagster_examples.toys.log_spew import log_spew
from dagster_examples.toys.many_events import many_events
from dagster_pandas.examples.pandas_hello_world.pipeline import pandas_hello_world

from dagster import RepositoryDefinition, ScheduleDefinition
from dagster.utils import file_relative_path


def define_repo():
    many_events_every_minute = ScheduleDefinition(
        name="many_events_every_min",
        cron_schedule="* * * * *",
        execution_params={
            "environmentConfigData": {"storage": {"filesystem": {}}},
            "selector": {"name": "many_events", "solidSubset": None},
            "mode": "default",
        },
    )

    log_spew_hourly = ScheduleDefinition(
        name="log_spew_hourly",
        cron_schedule="0 0 * * *",
        execution_params={
            "environmentConfigData": {"storage": {"filesystem": {}}},
            "selector": {"name": "log_spew", "solidSubset": None},
            "mode": "default",
        },
    )

    pandas_hello_world_hourly = ScheduleDefinition(
        name="pandas_hello_world_hourly",
        cron_schedule="* * * * *",
        execution_params={
            "environmentConfigData": {
                "solids": {
                    "sum_solid": {
                        "inputs": {
                            "num": {
                                "csv": {
                                    "path": file_relative_path(
                                        __file__, "../pandas_hello_world/data/num.csv"
                                    )
                                }
                            }
                        }
                    }
                }
            },
            "selector": {"name": "pandas_hello_world", "solidSubset": None},
            "mode": "default",
        },
    )

    return RepositoryDefinition(
        name='experimental_repository',
        pipeline_defs=[log_spew, many_events, pandas_hello_world],
        experimental={
            'scheduler': SystemCronScheduler,
            'schedule_defs': [many_events_every_minute, log_spew_hourly, pandas_hello_world_hourly],
        },
    )
