from collections import OrderedDict
import uuid

from dagster.core.execution_context import (
    ExecutionContext,
)

# pylint: disable=W0212


def test_noarg_ctor():
    context = ExecutionContext.create_for_test()
    assert uuid.UUID(context.run_id)
