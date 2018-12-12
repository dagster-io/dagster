from __future__ import print_function
from dagster import check

from dagster.utils.indenting_printer import IndentingPrinter

from .types import DagsterType


def print_type(dagster_type, print_fn=print):
    check.inst_param(dagster_type, 'dagster_type', DagsterType)
    check.callable_param(print_fn, 'print_fn')

    printer = IndentingPrinter(printer=print_fn)
    _do_print(dagster_type, printer)
    printer.line('')


def _do_print(dagster_type, printer):
    if dagster_type.is_list:
        printer.append('[')
        _do_print(dagster_type.inner_type, printer)
        printer.append(']')
    elif dagster_type.is_nullable:
        _do_print(dagster_type.inner_type, printer)
        printer.append('?')
    elif dagster_type.is_dict:
        printer.line('{')
        with printer.with_indent():
            for name, field in sorted(dagster_type.fields.items()):
                if field.is_optional:
                    printer.append(name + '?: ')
                else:
                    printer.append(name + ': ')
                _do_print(field.dagster_type, printer)
                printer.line('')

        printer.append('}')
    elif dagster_type.is_named:
        printer.append(dagster_type.name)
    else:
        check.failed('not supported')


def print_type_to_string(dagster_type):
    prints = []

    def _push(text):
        prints.append(text)

    print_type(dagster_type, _push)

    return '\n'.join(prints)
