'''
We start with a basic hello world here just to get a structure set up
'''
from dagster import PipelineDefinition, solid


@solid
def hello_world(context):
    context.log.info('Hello World!')


def define_pyspark_pagerank_step_one():
    return PipelineDefinition(name='pyspark_pagerank_step_one', solids=[hello_world])


if __name__ == '__main__':
    from dagster import execute_pipeline

    execute_pipeline(define_pyspark_pagerank_step_one())
