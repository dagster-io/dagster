from dagster_test.toys.nothing_input import nothing_job


def test_nothing_input():
    nothing_job.execute_in_process()
