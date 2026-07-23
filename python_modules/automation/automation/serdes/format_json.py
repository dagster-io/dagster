import json
from typing import Any

from automation.serdes.registry import Registry


def types_to_json(registry: Registry) -> dict[str, Any]:
    return {
        "objects": {
            name: {
                "typename": t.typename,
                "class_name": t.class_name,
                "storage_name": t.storage_name,
                "class_type": t.class_type,
                "serializer_type": t.serializer_type,
                "fields": [{"name": f.name, "type": f.type_str} for f in t.fields],
                "field_count": len(t.fields),
                "base_classes": t.base_classes,
                "field_mappings": t.field_mappings,
                "old_fields": t.old_fields,
                "skip_when_empty": t.skip_when_empty,
                "skip_when_none": t.skip_when_none,
                "is_record": t.is_record,
            }
            for name, t in registry.types.items()
        },
        "enums": {
            name: {
                "typename": e.typename,
                "enum_name": e.enum_name,
                "storage_name": e.storage_name,
                "class_type": e.class_type,
                "members": e.members,
            }
            for name, e in registry.enums.items()
        },
        "unions": {
            name: {
                "typename": u.typename,
                "base_class": u.base_class,
                "implementations": u.implementations,
            }
            for name, u in registry.unions.items()
        },
        "builtins": {
            name: {
                "typename": b.typename,
                "description": b.description,
            }
            for name, b in registry.builtins.items()
        },
        "stats": {
            "total_objects": len(registry.types),
            "total_enums": len(registry.enums),
            "total_unions": len(registry.unions),
            "total_builtins": len(registry.builtins),
        },
    }


def format_json(registry: Registry) -> str:
    return json.dumps(types_to_json(registry), indent=2)
