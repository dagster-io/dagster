import re
from collections.abc import Sequence

from automation.serdes.models import BuiltinType, SerdesEnum, SerdesObject, SerdesUnion


def simplify_type_str(type_str: str) -> str:
    if not type_str:
        return type_str

    result = type_str.replace("typing.", "")

    def simplify_name(match):
        full_name = match.group(0)
        parts = full_name.split(".")
        return parts[-1]

    result = re.sub(
        r"\b[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)+\.[A-Z][a-zA-Z0-9_]*\b",
        simplify_name,
        result,
    )

    return result


def format_enum_detail(serdes_enum: SerdesEnum) -> str:
    lines = []
    lines.append(f"{serdes_enum.typename}")
    lines.append(f"  Storage Name: {serdes_enum.storage_name}")
    lines.append(f"  Type: {serdes_enum.class_type}")
    lines.append(f"  Members: {', '.join(serdes_enum.members)}")
    return "\n".join(lines)


def format_type_detail(serdes_type: SerdesObject, simplify: bool) -> str:
    lines = []
    lines.append(f"{serdes_type.typename}")
    lines.append(f"  Storage Name: {serdes_type.storage_name}")
    lines.append(f"  Type: {serdes_type.class_type}")
    lines.append(f"  Serializer: {serdes_type.serializer_type}")

    if serdes_type.base_classes:
        lines.append(f"  Base Classes: {', '.join(serdes_type.base_classes)}")

    if serdes_type.fields:
        lines.append(f"  Fields ({len(serdes_type.fields)}):")
        for field in serdes_type.fields:
            if field.type_str:
                display_type = simplify_type_str(field.type_str) if simplify else field.type_str
                lines.append(f"    - {field.name}: {display_type}")
            else:
                lines.append(f"    - {field.name}")

    if serdes_type.field_mappings:
        lines.append("  Field Mappings:")
        for field, storage in serdes_type.field_mappings.items():
            lines.append(f"    {field} → {storage}")

    if serdes_type.old_fields:
        lines.append("  Old Fields (for backward compat):")
        for field, default in serdes_type.old_fields.items():
            lines.append(f"    {field} = {default}")

    if serdes_type.skip_when_empty:
        lines.append(f"  Skip When Empty: {', '.join(serdes_type.skip_when_empty)}")

    if serdes_type.skip_when_none:
        lines.append(f"  Skip When None: {', '.join(serdes_type.skip_when_none)}")

    return "\n".join(lines)


def format_union_detail(serdes_union: SerdesUnion) -> str:
    lines = []
    lines.append(f"{serdes_union.typename}")
    lines.append(f"  Type: {serdes_union.base_class}")
    lines.append(f"  Implementations ({len(serdes_union.implementations)}):")
    lines.extend(f"    - {impl}" for impl in serdes_union.implementations)
    return "\n".join(lines)


def format_builtin_detail(builtin: BuiltinType) -> str:
    lines = []
    lines.append(f"{builtin.typename}")
    lines.append(f"  Description: {builtin.description}")
    return "\n".join(lines)


def format_simple_list(
    items: Sequence[SerdesObject | SerdesEnum | SerdesUnion | BuiltinType],
) -> str:
    lines = [f"  {item.typename}" for item in items]
    return "\n".join(lines)


def format_detail(item: SerdesObject | SerdesEnum | SerdesUnion | BuiltinType) -> str:
    if isinstance(item, SerdesEnum):
        return format_enum_detail(item)
    elif isinstance(item, SerdesUnion):
        return format_union_detail(item)
    elif isinstance(item, BuiltinType):
        return format_builtin_detail(item)
    else:
        return format_type_detail(item, simplify=True)


def format_details(items: Sequence[SerdesObject | SerdesEnum | SerdesUnion | BuiltinType]) -> str:
    lines = []
    for item in items:
        lines.append(format_detail(item))
        lines.append("")
    return "\n".join(lines)
