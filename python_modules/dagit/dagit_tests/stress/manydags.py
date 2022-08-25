from dagit_tests.stress.dag_gen import generate_job

from dagster import repository


@repository
def dagit_stress_many_jobs():
    jobs = []
    for i in range(1500):
        jobs.append(generate_job(f"job_{i}", 50))
    return jobs
