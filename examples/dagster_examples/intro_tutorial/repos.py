from dagster import lambda_solid, PipelineDefinition, RepositoryDefinition


@lambda_solid
def hello_world():
    pass


def define_repo_demo_pipeline():
    return PipelineDefinition(name='repo_demo_pipeline', solids=[hello_world])


def define_repo():
    return RepositoryDefinition(
        name='demo_repository',
        # Note that we pass the function itself, rather than call the function.
        # This allows us to construct pipelines on demand.
        pipeline_dict={'repo_demo_pipeline': define_repo_demo_pipeline},
    )
