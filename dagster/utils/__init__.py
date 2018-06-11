from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401
import inspect

from dagster import check


def has_context_argument(fn):
    check.callable_param(fn, 'fn')

    argspec = inspect.getfullargspec(fn)
    return 'context' in argspec[0]


def make_context_arg_optional(fn):
    check.callable_param(fn, 'fn')
    # make this idempotent during the transition
    if fn.__name__ == '__wrapper_with_context':
        return fn
    check.invariant(fn.__name__ != '__wrapper_with_context')

    if not has_context_argument(fn):

        def __wrapper_with_context(*args, context, **kwargs):
            check.not_none_param(context, 'context')
            return fn(*args, **kwargs)

        return __wrapper_with_context
    else:
        return fn
