import uuid

from dagster.utils.test import create_test_runtime_execution_context

# pylint: disable=W0212


def test_noarg_ctor():
    context = create_test_runtime_execution_context()
    assert uuid.UUID(context.run_id)
