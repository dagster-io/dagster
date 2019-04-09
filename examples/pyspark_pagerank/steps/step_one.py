from dagster import PipelineDefinition, solid


@solid
def hello_world(context):
    context.log.info('Hello World!')


def define_pagerank_pipeline_step_one():
    return PipelineDefinition(name='pagerank_pipeline_step_one', solids=[hello_world])
