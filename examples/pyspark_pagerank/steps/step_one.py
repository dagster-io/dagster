from dagster import PipelineDefinition, solid


@solid
def hello_world(context):
    context.log.info('Hello World!')


def define_pyspark_pagerank_step_one():
    return PipelineDefinition(
        name='pyspark_pagerank_step_one', solids=[hello_world]
    )
