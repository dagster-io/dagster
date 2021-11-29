from dagster import repository


def get_airline_demo_pipelines():
    from airline_demo.pipelines import (
        airline_demo_ingest_pipeline,
        airline_demo_warehouse_pipeline,
    )

    return [
        airline_demo_ingest_pipeline,
        airline_demo_warehouse_pipeline,
    ]


def define_internal_dagit_repository():

    # Lazy import here to prevent deps issues
    @repository
    def internal_dagit_repository():

        pipeline_defs = get_airline_demo_pipelines()

        return pipeline_defs

    return internal_dagit_repository
