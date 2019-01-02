from dagster.utils import script_relative_path
from dagster.utils.black import black_test, perform_black_test


@black_test
def test_all_dagster_formatting():
    # This currently does all python code in monorepo
    # About 3.5 seconds on my machine
    target_dir = script_relative_path('../../..')
    perform_black_test(target_dir)
