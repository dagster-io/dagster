watch:
	watchmedo shell-command --recursive --patterns="*.py" -i "*.pyc"  --command \
	"pytest -vv "\
	"dagster/dagster/check/check_tests "\
	"dagster/dagster/cli/cli_tests "\
	"dagster/dagster/core/core_tests "\
	"dagster/dagster/dagster_examples/dagster_examples_tests "\
	"dagster/dagster/pandas/pandas_tests "\
	"dagster/dagster/sqlalchemy/sqlalchemy_tests "\
	"dagster/dagster/utils/utils_tests "\
	"dagster/dagster_tests "\
	"dagit/dagit_tests "\
	"dagster-ge/dagster_ge_tests " \
	--drop dagster/dagster dagster/dagster_tests/ dagster-ge/dagster_ge dagster-ge/dagster_ge_tests
	
yapf:
	find . -name "*.py" | grep -v ".tox" | grep -v ".vscode" | xargs yapf -i
		

