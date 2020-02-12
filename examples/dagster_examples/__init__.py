from dagster import ScheduleDefinition, file_relative_path, schedules


@schedules
def define_scheduler():
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


def define_demo_repo():
    # Lazy import here to prevent deps issues

    from dagster import RepositoryDefinition
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
    from dagster_examples.airline_demo.pipelines import (
        airline_demo_ingest_pipeline,
        airline_demo_warehouse_pipeline,
    )
    from dagster_examples.event_pipeline_demo.pipelines import event_ingest_pipeline
    from dagster_examples.pyspark_pagerank.pyspark_pagerank_pipeline import pyspark_pagerank
    from dagster_examples.toys.unreliable import unreliable_pipeline

    # from dagster_pandas.examples import papermill_pandas_hello_world_pipeline
    from dagster_examples.jaffle_dbt.jaffle import jaffle_pipeline

    return RepositoryDefinition(
        name='hello_cereal_repository',
        pipeline_defs=[
            pandas_hello_world_pipeline_with_read_csv,
            pandas_hello_world_pipeline,
            sleepy_pipeline,
            error_monster,
            log_spew,
            many_events,
            composition,
            airline_demo_ingest_pipeline,
            airline_demo_warehouse_pipeline,
            event_ingest_pipeline,
            pyspark_pagerank,
            # papermill_pandas_hello_world_pipeline,
            jaffle_pipeline,
            stdout_spew_pipeline,
            unreliable_pipeline,
        ],
    )
