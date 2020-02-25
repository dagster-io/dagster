from __future__ import print_function

from dagster import check
from dagster.utils.indenting_printer import IndentingPrinter

from .config_type import ConfigType, ConfigTypeKind
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


def _do_print(config_type, printer, with_lines=True):
    line_break_fn = printer.line if with_lines else lambda string: printer.append(string + ' ')

    kind = config_type.kind

    if kind == ConfigTypeKind.ARRAY:
        printer.append('[')
        _do_print(config_type.inner_type, printer)
        printer.append(']')
    elif kind == ConfigTypeKind.NONEABLE:
        _do_print(config_type.inner_type, printer)
        printer.append('?')
    elif kind == ConfigTypeKind.SCALAR_UNION:
        printer.append('(')
        _do_print(config_type.scalar_type, printer)
        printer.append(' | ')
        _do_print(config_type.non_scalar_type, printer)
        printer.append(')')
    elif ConfigTypeKind.has_fields(kind):
        line_break_fn('{')
        with printer.with_indent():
            for name, field in sorted(config_type.fields.items()):
                if field.is_required:
                    printer.append(name + ': ')
                else:
                    printer.append(name + '?: ')
                _do_print(
                    field.config_type, printer, with_lines=with_lines,
                )
                line_break_fn('')

        printer.append('}')
    elif config_type.given_name:
        printer.append(config_type.given_name)
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
