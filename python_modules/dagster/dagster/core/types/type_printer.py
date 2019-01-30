from __future__ import print_function
from dagster import check

from dagster.utils.indenting_printer import IndentingPrinter

from .config import ConfigType
from .field import resolve_to_config_type


def print_type(config_type, print_fn=print, with_lines=True):
    check.inst_param(config_type, 'config_type', ConfigType)
    check.callable_param(print_fn, 'print_fn')

    if with_lines:
        printer = IndentingPrinter(printer=print_fn)
    else:
        printer = IndentingPrinter(printer=print_fn, indent_level=0)
    _do_print(config_type, printer, with_lines=with_lines)
    printer.line('')


def _do_print(config_type, printer, with_lines=True, shortcut_named=False):
    line_break_fn = printer.line if with_lines else lambda string: printer.append(string + ' ')

    if config_type.is_list:
        printer.append('[')
        _do_print(config_type.inner_type, printer)
        printer.append(']')
    elif config_type.is_nullable:
        _do_print(config_type.inner_type, printer)
        printer.append('?')
    elif config_type.has_fields:
        if config_type.name and shortcut_named:
            printer.append(config_type.name)
        else:
            line_break_fn('{')
            with printer.with_indent():
                for name, field in sorted(config_type.fields.items()):
                    if field.is_optional:
                        printer.append(name + '?: ')
                    else:
                        printer.append(name + ': ')
                    _do_print(
                        field.config_type, printer, with_lines=with_lines, shortcut_named=True
                    )
                    line_break_fn('')

            printer.append('}')
    elif config_type.name:
        printer.append(config_type.name)
    else:
        check.failed('not supported')


def print_type_to_string(dagster_type):
    config_type = resolve_to_config_type(dagster_type)
    return print_config_type_to_string(config_type)


def print_config_type_to_string(config_type, with_lines=True):
    prints = []

    def _push(text):
        prints.append(text)

    print_type(config_type, _push, with_lines=with_lines)

    if with_lines:
        return '\n'.join(prints)
    else:
        return ' '.join(prints)
