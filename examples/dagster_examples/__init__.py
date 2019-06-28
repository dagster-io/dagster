def define_demo_repo():
    # Lazy import here to prevent deps issues

    from dagster import RepositoryDefinition
    from dagster_examples.toys.error_monster import error_monster
    from dagster_examples.toys.sleepy import sleepy_pipeline
    from dagster_examples.toys.log_spew import define_spew_pipeline
    from dagster_examples.toys.many_events import many_events
    from dagster_examples.toys.composition import composition
    from dagster_examples.toys.pandas_hello_world import pandas_hello_world_pipeline
    from dagster_examples.airline_demo.pipelines import (
        define_airline_demo_ingest_pipeline,
        define_airline_demo_warehouse_pipeline,
    )
    from dagster_examples.event_pipeline_demo.pipelines import event_ingest_pipeline
    from dagster_examples.pyspark_pagerank.pyspark_pagerank_pipeline import pyspark_pagerank
    from dagster_pandas.examples import define_papermill_pandas_hello_world_pipeline

    return RepositoryDefinition(
        name='demo_repository',
        pipeline_dict={
            'pandas_hello_world_pipeline': pandas_hello_world_pipeline,
            'sleepy': sleepy_pipeline,
            'error_monster': error_monster,
            'log_spew': define_spew_pipeline,
            'many_events': many_events,
            'composition': composition,
            'airline_demo_ingest_pipeline': define_airline_demo_ingest_pipeline,
            'airline_demo_warehouse_pipeline': define_airline_demo_warehouse_pipeline,
            'event_ingest_pipeline': event_ingest_pipeline,
            'pyspark_pagerank': pyspark_pagerank,
            'papermill_pandas_hello_world_pipeline': define_papermill_pandas_hello_world_pipeline,
        },
    )
