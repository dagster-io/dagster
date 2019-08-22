from dagster import RepositoryDefinition, pipeline, solid


@solid
def hello_world(_):
    pass


@pipeline
def repo_demo_pipeline():
    hello_world()  # pylint: disable=no-value-for-parameter


def define_repo():
    return RepositoryDefinition(
        name='demo_repository',
        # Note that we can pass a function, rather than pipeline instance.
        # This allows us to construct pipelines on demand.
        pipeline_dict={'repo_demo_pipeline': lambda: repo_demo_pipeline},
    )
