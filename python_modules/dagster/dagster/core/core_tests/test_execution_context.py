from collections import OrderedDict
import uuid

from dagster.core.execution_context import (
    ExecutionContext,
)

# pylint: disable=W0212


def test_noarg_ctor():
    context = ExecutionContext()
    assert set(context._context_stack.keys()) == set(['run_id'])
    assert uuid.UUID(context.get_context_value('run_id'))
    assert uuid.UUID(context.run_id)
