from dagster import Definitions
from dagster._utils import file_relative_path
from dagster_ge.factory import GEContextResource

from with_great_expectations.ge_demo import payroll_data

defs = Definitions(
    jobs=[payroll_data],
    resources={
        "ge_data_context": GEContextResource(
            ge_root_dir=file_relative_path(__file__, "./great_expectations")
        ),
    },
)
