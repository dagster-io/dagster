from dagster import lambda_solid, pipeline, RepositoryDefinition


@lambda_solid
def hello_world():
    pass


@pipeline
def repo_demo_pipeline(_):
    hello_world()


def define_repo():
    return RepositoryDefinition(
        name='demo_repository',
        # Note that we can pass a function, rather than pipeline instance.
        # This allows us to construct pipelines on demand.
        pipeline_dict={'repo_demo_pipeline': lambda: repo_demo_pipeline},
    )
