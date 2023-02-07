from dagster import Definitions

from with_great_expectations.ge_demo import payroll_data

defs = Definitions(jobs=[payroll_data])
