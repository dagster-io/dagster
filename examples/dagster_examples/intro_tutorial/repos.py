from dagster import lambda_solid, pipeline, RepositoryDefinition


@lambda_solid
def hello_world():
    pass


@pipeline
def repo_demo_pipeline(_):
    hello_world()


def define_repo_demo_pipeline():
    return repo_demo_pipeline


def define_repo():
    return RepositoryDefinition(
        name='demo_repository',
        # Note that we pass the function itself, rather than call the function.
        # This allows us to construct pipelines on demand.
        pipeline_dict={'repo_demo_pipeline': define_repo_demo_pipeline},
    )
