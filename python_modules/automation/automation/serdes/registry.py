import re
import sys
from abc import ABC
from typing import Any, get_type_hints

import click
from dagster_shared.check.record import is_record

from automation.serdes.models import BuiltinType, SerdesEnum, SerdesField, SerdesObject, SerdesUnion


def _extract_type_string(type_annotation: Any) -> str:
    type_str = str(type_annotation)
    if type_str.startswith("<class '") and type_str.endswith("'>"):
        type_str = type_str[8:-2]
    return type_str


def _extract_referenced_types(type_str: str) -> set[str]:
    if not type_str:
        return set()

    pattern = r"\b[A-Z][a-zA-Z0-9_]*\b"
    matches = re.findall(pattern, type_str)

    # Filter out common generics but keep the special ones we track
    common_generics = {
        "Optional",
        "Union",
        "Sequence",
        "Mapping",
        "List",
        "Dict",
        "Tuple",
        "Callable",
    }
    return set(m for m in matches if m not in common_generics)


class Registry:
    def __init__(self) -> None:
        self.types: dict[str, SerdesObject] = {}
        self.enums: dict[str, SerdesEnum] = {}
        self.unions: dict[str, SerdesUnion] = {}
        self.builtins: dict[str, BuiltinType] = {}

    @property
    def size(self):
        return len(self.types) + len(self.enums) + len(self.unions) + len(self.builtins)

    def get(self, typename: str):
        return self.types.get(
            typename,
            self.enums.get(typename, self.unions.get(typename, self.builtins.get(typename))),
        )


def scan_registry(whitelist_map) -> Registry:
    registry = Registry()

    # Scan object serializers
    for class_name, serializer in sorted(whitelist_map.object_serializers.items()):
        storage_name = serializer.get_storage_name()
        class_type = f"{serializer.klass.__module__}.{serializer.klass.__qualname__}"
        serializer_type = type(serializer).__name__
        klass = serializer.klass

        # Extract base classes
        base_classes = []
        for base in klass.__mro__[1:]:
            # Skip standard library and @record internals
            if base.__module__ in ("builtins", "abc"):
                continue
            if base.__module__ == "dagster_shared.record" and base.__name__.startswith("_"):
                continue
            if base is tuple or base is object:
                continue
            # Skip if it's the class itself (can happen with @record)
            if base.__name__ == class_name:
                continue
            # Only include ABC bases
            if issubclass(base, ABC):
                base_classes.append(base.__name__)

        # Extract field information
        constructor_params = serializer.constructor_param_names

        # Extract field types using get_type_hints with the module namespace
        # to properly resolve forward references
        fields = []
        try:
            # Provide the class's module globals to resolve forward references
            module_globals = vars(sys.modules[klass.__module__])
            type_hints = get_type_hints(klass, globalns=module_globals)

            for field_name in constructor_params:
                # Skip 'cls' and '_cls'
                if field_name in ("cls", "_cls"):
                    continue

                type_str = None
                if field_name in type_hints:
                    type_annotation = type_hints[field_name]
                    type_str = _extract_type_string(type_annotation)

                fields.append(SerdesField(name=field_name, type_str=type_str))
        except Exception as e:
            click.echo(f"Warning: get_type_hints failed for {klass.__name__}: {e}", err=True)
            # Fallback to __annotations__ if get_type_hints fails
            annotations = getattr(klass, "__annotations__", {})
            for field_name in constructor_params:
                if field_name in ("cls", "_cls"):
                    continue

                type_str = None
                if field_name in annotations:
                    type_annotation = annotations[field_name]
                    type_str = _extract_type_string(type_annotation)

                fields.append(SerdesField(name=field_name, type_str=type_str))

        # Extract compatibility info
        field_mappings = (
            dict(serializer.storage_field_names) if serializer.storage_field_names else None
        )
        old_fields = dict(serializer.old_fields) if serializer.old_fields else None
        skip_when_empty = (
            list(serializer.skip_when_empty_fields) if serializer.skip_when_empty_fields else None
        )
        skip_when_none = (
            list(serializer.skip_when_none_fields) if serializer.skip_when_none_fields else None
        )

        # Check if this is a @record class
        is_record_class = is_record(klass)

        registry.types[class_name] = SerdesObject(
            typename=class_name,
            class_name=class_name,
            storage_name=storage_name,
            class_type=class_type,
            serializer_type=serializer_type,
            fields=fields,
            base_classes=base_classes if base_classes else None,
            field_mappings=field_mappings,
            old_fields=old_fields,
            skip_when_empty=skip_when_empty,
            skip_when_none=skip_when_none,
            is_record=is_record_class,
        )

    # Scan enum serializers
    for enum_name, serializer in sorted(whitelist_map.enum_serializers.items()):
        storage_name = serializer.get_storage_name()
        class_type = f"{serializer.klass.__module__}.{serializer.klass.__qualname__}"
        members = [m.name for m in serializer.klass]

        registry.enums[enum_name] = SerdesEnum(
            typename=enum_name,
            enum_name=enum_name,
            storage_name=storage_name,
            class_type=class_type,
            members=members,
        )

    # Discover union types (abstract base classes with whitelisted implementations)
    base_to_implementations: dict[str, list[str]] = {}

    for class_name, serializer in whitelist_map.object_serializers.items():
        klass = serializer.klass

        # Walk MRO to find abstract base classes
        for base in klass.__mro__[1:]:  # Skip self
            # Filter out standard library and @record internals
            if base.__module__ in ("builtins", "abc"):
                continue
            if base.__module__ == "dagster_shared.record" and base.__name__.startswith("_"):
                continue
            if base is tuple or base is object:
                continue

            # Check if it's an ABC
            if issubclass(base, ABC):
                base_name = base.__name__
                full_base = f"{base.__module__}.{base.__qualname__}"

                # Skip if this base is also whitelisted (it's a concrete type)
                if base_name in whitelist_map.object_serializers:
                    continue

                if full_base not in base_to_implementations:
                    base_to_implementations[full_base] = []
                base_to_implementations[full_base].append(class_name)

    # Create SerdesUnion for each discovered base
    for base_class, implementations in sorted(base_to_implementations.items()):
        # Extract typename from base_class (module.path.ClassName -> ClassName)
        typename = base_class.split(".")[-1]
        registry.unions[typename] = SerdesUnion(
            typename=typename,
            base_class=base_class,
            implementations=sorted(implementations),
        )

    # Register builtin types that we track
    registry.builtins["Any"] = BuiltinType(
        typename="Any", description="Any type - can hold any serializable value"
    )
    registry.builtins["Set"] = BuiltinType(
        typename="Set", description="Set type - unordered collection of unique elements"
    )
    registry.builtins["AbstractSet"] = BuiltinType(
        typename="AbstractSet", description="Abstract set type from collections.abc"
    )
    registry.builtins["FrozenSet"] = BuiltinType(
        typename="FrozenSet", description="Immutable set type"
    )

    return registry


def list_descendants(typename: str, registry: Registry) -> Registry:
    """Build a registry containing only the typename and its descendants."""
    visited = set()
    to_visit = [typename]

    result = Registry()

    while to_visit:
        current = to_visit.pop(0)
        if current in visited:
            continue
        visited.add(current)

        if current in registry.types:
            serdes_type = registry.types[current]
            result.types[current] = serdes_type

            for field in serdes_type.fields:
                if field.type_str:
                    referenced = _extract_referenced_types(field.type_str)
                    to_visit.extend(ref for ref in referenced if ref not in visited)
        elif current in registry.enums:
            result.enums[current] = registry.enums[current]
        elif current in registry.unions:
            serdes_union = registry.unions[current]
            result.unions[current] = serdes_union
            to_visit.extend(impl for impl in serdes_union.implementations if impl not in visited)
        elif current in registry.builtins:
            result.builtins[current] = registry.builtins[current]

    return result
