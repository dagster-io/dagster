from typing import List, Optional

import dagster._check as check
from dagster._utils.indenting_printer import IndentingPrinter

from .config_type import ConfigType, ConfigTypeKind
from .field import normalize_config_type
from .snap import ConfigSchemaSnap


def config_type_to_string(
    config_type: Optional[ConfigType] = None,
    config_type_key: Optional[str] = None,
    config_schema_snapshot: Optional[ConfigSchemaSnap] = None,
    with_lines: bool = True,
) -> str:

    if config_type is not None:
        _config_type = normalize_config_type(config_type)
        return config_type_to_string(
            config_type_key=_config_type.key,
            config_schema_snapshot=_config_type.get_schema_snapshot(),
            with_lines=with_lines,
        )
    elif config_type_key is not None and config_schema_snapshot is not None:
        check.inst_param(config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnap)
        check.str_param(config_type_key, "config_type_key")

        buffer: List[str] = []

        def push(text: str) -> None:
            buffer.append(text)

        printer = (
            IndentingPrinter(printer=push)
            if with_lines
            else IndentingPrinter(printer=push, indent_level=0)
        )
        _do_print(config_schema_snapshot, config_type_key, printer, with_lines=with_lines)
        printer.line("")

        separator = "\n" if with_lines else " "
        return separator.join(buffer)
    else:
        check.failed(
            "Must provide either config_type or config_type_key and config_schema_snapshot"
        )


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
            for field_snap in sorted(config_type_snap.fields):  # type: ignore
                name = check.not_none(field_snap.name)
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
