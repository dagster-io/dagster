import pytest

# pytest rewrites `assert` in test cases to give additional info for debugging. This class isn't a
# test case itself, but it contains the asserts that are used to test the various run storages.
# We need to explicitly inform pytest that these asserts are part of the test cases, and not just
# arbitrary library calls.
pytest.register_assert_rewrite("dagster_tests.core_tests.storage_tests.utils.run_storage")
from . import run_storage  # isort:skip
