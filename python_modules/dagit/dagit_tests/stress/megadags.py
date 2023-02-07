from dagster import repository

from dagit_tests.stress.dag_gen import generate_job


@repository
def dagit_stress_tests():
    return [
        generate_job("1000_nodes", 1000, 1.0),
        generate_job("2500_nodes", 2500, 1.0),
    ]
