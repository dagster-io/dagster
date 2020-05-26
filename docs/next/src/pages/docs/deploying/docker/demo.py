from dagster import RepositoryDefinition


def define_demo_repo():
    return RepositoryDefinition(name='demo_repo')
