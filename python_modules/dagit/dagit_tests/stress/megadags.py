from dagit_tests.stress.dag_gen import generate_pipeline
from dagster import repository


@repository
def dagit_stress_tests():
    return [generate_pipeline("1000_nodes", 1000, 1.0)]
