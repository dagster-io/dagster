from __future__ import print_function
from dagster import check

from dagster.utils.indenting_printer import IndentingPrinter

from .config import ConfigType, resolve_to_config_type


def print_type(config_type, print_fn=print):
    check.inst_param(config_type, 'config_type', ConfigType)
    check.callable_param(print_fn, 'print_fn')

    printer = IndentingPrinter(printer=print_fn)
    _do_print(config_type, printer)
    printer.line('')


def _do_print(config_type, printer):
    if config_type.is_list:
        printer.append('[')
        _do_print(config_type.inner_type, printer)
        printer.append(']')
    elif config_type.is_nullable:
        _do_print(config_type.inner_type, printer)
        printer.append('?')
    elif config_type.has_fields:
        printer.line('{')
        with printer.with_indent():
            for name, field in sorted(config_type.fields.items()):
                if field.is_optional:
                    printer.append(name + '?: ')
                else:
                    printer.append(name + ': ')
                _do_print(field.config_type, printer)
                printer.line('')

        printer.append('}')
    elif config_type.is_named:
        printer.append(config_type.name)
    else:
        check.failed('not supported')


def print_type_to_string(dagster_type):
    config_type = resolve_to_config_type(dagster_type)
    prints = []

    def _push(text):
        prints.append(text)

    print_type(config_type, _push)

    return '\n'.join(prints)
