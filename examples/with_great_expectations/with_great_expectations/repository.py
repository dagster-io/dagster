from with_great_expectations.ge_demo import payroll_data

from dagster import repository


@repository
def with_great_expectations():
    return [payroll_data]
