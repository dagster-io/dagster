from dagster import repository
from with_great_expectations.ge_demo import payroll_data


@repository
def with_great_expectations():
    return [payroll_data]
