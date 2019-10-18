from dagit_tests.stress.dag_gen import generate_pipeline

from dagster import RepositoryDefinition


def define_repository():

    return RepositoryDefinition(
        name='dagit_stress_tests', pipeline_defs=[generate_pipeline('1000_nodes', 1000, 1.0)]
    )
