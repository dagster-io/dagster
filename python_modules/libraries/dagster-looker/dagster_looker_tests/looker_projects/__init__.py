from pathlib import Path

projects_path = Path(__file__).joinpath("..").resolve()

test_retail_demo_path = projects_path.joinpath("retail_demo")
test_exception_derived_table_path = projects_path.joinpath("test_exception_derived_table")
