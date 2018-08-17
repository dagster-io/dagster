watch:
	watchmedo shell-command --recursive --patterns="*.py" -i "*.pyc"  --command \
	"pytest -s -vv "\
	"dagster/dagster/check/check_tests "\
	"dagster/dagster/core/core_tests "\
	"dagster/dagster/dagster_examples/dagster_examples_tests "\
	"dagster/dagster/pandas_kernel/pandas_kernel_tests "\
	"dagster/dagster/sqlalchemy_kernel/sqlalchemy_kernel_tests "\
	"dagster/dagster/utils/utils_tests "\
	"dagster/dagster_tests "\
	"dagster-ge/dagster_ge_tests " \
	--drop dagster/dagster dagster/dagster_tests/ dagster-ge/dagster_ge dagster-ge/dagster_ge_tests
	
	
