from collections import OrderedDict
import uuid

from dagster.core.execution_context import (
    ExecutionContext,
    ReentrantContextInfo,
)

# pylint: disable=W0212


def test_noarg_ctor():
    context = ExecutionContext()
    assert context._context_stack == OrderedDict()


def test_for_run_ctor():
    context = ExecutionContext.for_run()
    assert uuid.UUID(context.get_context_value('run_id'))
    assert uuid.UUID(context.run_id)


def test_reentrant_info():
    context = ExecutionContext(reentrant_info=ReentrantContextInfo(OrderedDict()))
    assert context._context_stack == OrderedDict()


def test_reentrant_info_with_values():
    context = ExecutionContext(reentrant_info=ReentrantContextInfo(OrderedDict({'foo': 'bar'})))
    assert context._context_stack == OrderedDict({'foo': 'bar'})
    assert context.get_context_value('foo') == 'bar'
