from typing import Any, Callable, List

import dagster._check as check
from dagster._utils.indenting_printer import IndentingPrinter

from .config_type import ConfigType, ConfigTypeKind
from .field import normalize_config_type
from .snap import ConfigSchemaSnap


def _print_type_from_config_type(
    config_type: ConfigType, print_fn: Callable[[Any], None] = print, with_lines: bool = True
) -> None:
    check.inst_param(config_type, "config_type", ConfigType)
    _print_type(config_type.get_schema_snapshot(), config_type.key, print_fn, with_lines)


def _print_type(
    config_schema_snapshot: ConfigSchemaSnap,
    config_type_key: str,
    print_fn: Callable[[Any], None],
    with_lines: bool,
) -> None:
    check.inst_param(config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnap)
    check.str_param(config_type_key, "config_type_key")
    check.callable_param(print_fn, "print_fn")
    check.bool_param(with_lines, "with_lines")

    if with_lines:
        printer = IndentingPrinter(printer=print_fn)
    else:
        printer = IndentingPrinter(printer=print_fn, indent_level=0)
    _do_print(config_schema_snapshot, config_type_key, printer, with_lines=with_lines)
    printer.line("")


def _do_print(
    config_schema_snapshot: ConfigSchemaSnap,
    config_type_key: str,
    printer: IndentingPrinter,
    with_lines: bool = True,
) -> None:
    line_break_fn = printer.line if with_lines else lambda string: printer.append(string + " ")

    config_type_snap = config_schema_snapshot.get_config_type_snap(config_type_key)
    kind = config_type_snap.kind

    if kind == ConfigTypeKind.ARRAY:
        printer.append("[")
        _do_print(config_schema_snapshot, config_type_snap.inner_type_key, printer)
        printer.append("]")
    elif kind == ConfigTypeKind.NONEABLE:
        _do_print(config_schema_snapshot, config_type_snap.inner_type_key, printer)
        printer.append("?")
    elif kind == ConfigTypeKind.SCALAR_UNION:
        printer.append("(")
        _do_print(config_schema_snapshot, config_type_snap.scalar_type_key, printer)
        printer.append(" | ")
        _do_print(config_schema_snapshot, config_type_snap.non_scalar_type_key, printer)
        printer.append(")")
    elif kind == ConfigTypeKind.MAP:
        # e.g.
        # {
        #   [String]: Int
        # }
        line_break_fn("{")
        with printer.with_indent():
            printer.append("[")
            # In a Map, the given_name stores the optional key_label_name
            if config_type_snap.given_name:
                printer.append(f"{config_type_snap.given_name}: ")
            _do_print(config_schema_snapshot, config_type_snap.key_type_key, printer)
            printer.append("]: ")
            _do_print(
                config_schema_snapshot,
                config_type_snap.inner_type_key,
                printer,
                with_lines=with_lines,
            )
            line_break_fn("")
        printer.append("}")
    elif ConfigTypeKind.has_fields(kind):
        line_break_fn("{")
        with printer.with_indent():
            for field_snap in sorted(config_type_snap.fields):
                name = field_snap.name
                if field_snap.is_required:
                    printer.append(name + ": ")
                else:
                    printer.append(name + "?: ")
                _do_print(
                    config_schema_snapshot,
                    field_snap.type_key,
                    printer,
                    with_lines=with_lines,
                )
                line_break_fn("")

        printer.append("}")
    elif config_type_snap.given_name:
        printer.append(config_type_snap.given_name)
    else:
        check.failed("not supported")


def print_config_type_key_to_string(
    config_schema_snapshot: ConfigSchemaSnap, config_type_key: str, with_lines: bool = True
) -> str:
    prints: List[str] = []

    def _push(text: str) -> None:
        prints.append(text)

    _print_type(config_schema_snapshot, config_type_key, _push, with_lines)

    if with_lines:
        return "\n".join(prints)
    else:
        return " ".join(prints)


def print_config_type_to_string(config_type: ConfigType, with_lines: bool = True) -> str:
    prints = []

    def _push(text: str) -> None:
        prints.append(text)

    _print_type_from_config_type(normalize_config_type(config_type), _push, with_lines=with_lines)

    if with_lines:
        return "\n".join(prints)
    else:
        return " ".join(prints)
