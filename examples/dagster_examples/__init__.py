from dagster.core.scheduler import SchedulerHandle


def get_bay_bikes_schedules():
    from dagster_examples.bay_bikes.schedules import (
        daily_weather_ingest_schedule,
        monthly_trip_ingest_schedule,
    )

    return [daily_weather_ingest_schedule, monthly_trip_ingest_schedule]


def get_toys_schedules():
    from dagster import ScheduleDefinition, file_relative_path

    return [
        ScheduleDefinition(
            name="many_events_every_min",
            cron_schedule="* * * * *",
            pipeline_name='many_events',
            environment_dict_fn=lambda _: {"storage": {"filesystem": {}}},
        ),
        ScheduleDefinition(
            name="pandas_hello_world_hourly",
            cron_schedule="0 * * * *",
            pipeline_name="pandas_hello_world_pipeline",
            environment_dict_fn=lambda _: {
                'solids': {
                    'mult_solid': {
                        'inputs': {
                            'num_df': {
                                'csv': {
                                    'path': file_relative_path(
                                        __file__, "pandas_hello_world/data/num.csv"
                                    )
                                }
                            }
                        }
                    },
                    'sum_solid': {
                        'inputs': {
                            'num_df': {
                                'csv': {
                                    'path': file_relative_path(
                                        __file__, "pandas_hello_world/data/num.csv"
                                    )
                                }
                            }
                        }
                    },
                },
                "storage": {"filesystem": {}},
            },
        ),
    ]


def define_scheduler():
    # Done instead of using schedules to avoid circular dependency issues.
    return SchedulerHandle(schedule_defs=get_bay_bikes_schedules() + get_toys_schedules())


def get_toys_pipelines():
    from dagster_examples.toys.error_monster import error_monster
    from dagster_examples.toys.sleepy import sleepy_pipeline
    from dagster_examples.toys.log_spew import log_spew
    from dagster_examples.toys.stdout_spew import stdout_spew_pipeline
    from dagster_examples.toys.many_events import many_events
    from dagster_examples.toys.composition import composition
    from dagster_examples.toys.pandas_hello_world import (
        pandas_hello_world_pipeline,
        pandas_hello_world_pipeline_with_read_csv,
    )
    from dagster_examples.toys.unreliable import unreliable_pipeline

    return [
        composition,
        error_monster,
        log_spew,
        many_events,
        pandas_hello_world_pipeline,
        pandas_hello_world_pipeline_with_read_csv,
        sleepy_pipeline,
        stdout_spew_pipeline,
        unreliable_pipeline,
    ]


def get_airline_demo_pipelines():
    from dagster_examples.airline_demo.pipelines import (
        airline_demo_ingest_pipeline,
        airline_demo_warehouse_pipeline,
    )

    return [
        airline_demo_ingest_pipeline,
        airline_demo_warehouse_pipeline,
    ]


def get_event_pipelines():
    from dagster_examples.event_pipeline_demo.pipelines import event_ingest_pipeline

    return [event_ingest_pipeline]


def get_pyspark_pipelines():
    from dagster_examples.pyspark_pagerank.pyspark_pagerank_pipeline import pyspark_pagerank

    return [pyspark_pagerank]


def get_jaffle_pipelines():
    from dagster_examples.jaffle_dbt.jaffle import jaffle_pipeline

    return [jaffle_pipeline]


def get_bay_bikes_pipelines():
    from dagster_examples.bay_bikes.pipelines import generate_training_set_and_train_model

    return [generate_training_set_and_train_model]


def define_demo_repo():
    # Lazy import here to prevent deps issues
    from dagster import RepositoryDefinition

    pipeline_defs = (
        get_airline_demo_pipelines()
        + get_bay_bikes_pipelines()
        + get_event_pipelines()
        + get_jaffle_pipelines()
        + get_pyspark_pipelines()
        + get_toys_pipelines()
    )

    return RepositoryDefinition(name='internal-dagit-repository', pipeline_defs=pipeline_defs,)
