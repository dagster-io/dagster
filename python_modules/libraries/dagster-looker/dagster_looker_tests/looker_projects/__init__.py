from pathlib import Path

projects_path = Path(__file__).joinpath("..").resolve()

test_retail_demo_path = projects_path.joinpath("retail_demo")
test_exception_derived_table_path = projects_path.joinpath("test_exception_derived_table")
test_refinements = projects_path.joinpath("test_refinements")
test_extensions = projects_path.joinpath("test_extensions")
test_liquid_path = projects_path.joinpath("test_liquid")
test_union_no_distinct_path = projects_path.joinpath("test_union_no_distinct")
