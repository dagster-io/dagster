from typing import Any, Dict, List, Union


def get_example_value_for_type(schema_type: str, format_hint: str = None, constraints: Dict[str, Any] = None, property_name: str = None, is_array_item: bool = False) -> Any:
    """Generate example values based on JSON Schema type and constraints."""
    constraints = constraints or {}
    
    if schema_type == "string":
        # Property-specific examples for better UX (but not for array items)
        if not is_array_item and property_name == "name":
            return "Jane Doe"
        elif not is_array_item and property_name == "street":
            return "123 Main St"
        elif not is_array_item and property_name == "city":
            return "Boston"
        elif not is_array_item and property_name == "zip":
            return "02101"
        elif format_hint == "email":
            return "user@example.com"
        elif format_hint == "date":
            return "2023-12-31"
        elif format_hint == "uri":
            return "https://example.com"
        elif "pattern" in constraints:
            pattern = constraints["pattern"]
            if pattern == "^[A-Z]{3}-\\d{3}$":
                return "ABC-123"
            else:
                return "pattern_match"
        else:
            max_length = constraints.get("maxLength")
            if max_length and max_length <= 10:
                return "example"
            return "example_string"
    
    elif schema_type == "integer":
        # Property-specific examples (but not for array items)
        if not is_array_item and property_name == "age":
            return 30
        
        minimum = constraints.get("minimum")
        maximum = constraints.get("maximum")
        
        if minimum is not None and maximum is not None:
            return (minimum + maximum) // 2
        elif minimum is not None:
            return max(minimum, 42)
        elif maximum is not None:
            return max(1, maximum // 2)
        else:
            return 42
    
    elif schema_type == "number":
        minimum = constraints.get("minimum")
        maximum = constraints.get("maximum")
        
        if minimum is not None and maximum is not None:
            return (minimum + maximum) / 2
        elif minimum is not None:
            return max(minimum, 3.14)
        elif maximum is not None:
            return min(maximum, 3.14)
        else:
            return 3.14
    
    elif schema_type == "boolean":
        return True
    
    else:
        return "unknown_value"


def get_constraint_description(schema_type: str, constraints: Dict[str, Any]) -> str:
    """Generate human-readable constraint descriptions."""
    parts = []
    
    if schema_type == "string":
        if "minLength" in constraints:
            parts.append(f"Minimum length {constraints['minLength']}")
        if "maxLength" in constraints:
            parts.append(f"Maximum length {constraints['maxLength']}")
        if "pattern" in constraints:
            parts.append(f"Must match pattern: {constraints['pattern']}")
        if "format" in constraints:
            format_descriptions = {
                "email": "Valid email format",
                "date": "Valid date format (YYYY-MM-DD)",
                "uri": "Valid URI format",
                "uuid": "Valid UUID format"
            }
            parts.append(format_descriptions.get(constraints["format"], f"Valid {constraints['format']} format"))
    
    elif schema_type in ("integer", "number"):
        minimum = constraints.get("minimum")
        maximum = constraints.get("maximum")
        
        if minimum is not None and maximum is not None:
            parts.append(f"Must be >= {minimum} and <= {maximum}")
        elif minimum is not None:
            parts.append(f"Must be >= {minimum}")
        elif maximum is not None:
            parts.append(f"Must be <= {maximum}")
    
    elif schema_type == "array":
        if "minItems" in constraints:
            parts.append(f"minimum {constraints['minItems']} items")
        if "maxItems" in constraints:
            parts.append(f"maximum {constraints['maxItems']} items")
    
    return ", ".join(parts) if parts else ""


def get_object_description(property_name: str, schema: Dict[str, Any]) -> str:
    """Generate description for object properties."""
    if "description" in schema:
        return schema["description"]
    
    # Generate generic descriptions based on property name
    name_descriptions = {
        "address": "Address details",
        "user": "User details", 
        "config": "Configuration settings",
        "metadata": "Metadata information",
        "settings": "Settings configuration",
        "options": "Options configuration"
    }
    
    return name_descriptions.get(property_name, f"{property_name.title()} details")


def get_array_description(items_schema: Dict[str, Any]) -> str:
    """Generate description for array properties."""
    items_type = items_schema.get("type", "unknown")
    
    if items_type == "object":
        return "List of object items"
    else:
        return f"List of {items_type} items"


def format_yaml_value(value: Any, indent_level: int = 0) -> str:
    """Format a value as YAML with proper indentation."""
    indent = "  " * indent_level
    
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        if not value:
            return "[]"
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{indent}- {format_dict_as_yaml(item, indent_level + 1, is_array_item=True)}")
            else:
                lines.append(f"{indent}- {format_yaml_value(item, 0)}")
        return "\n".join(lines)
    elif isinstance(value, dict):
        return format_dict_as_yaml(value, indent_level)
    else:
        return str(value)


def format_dict_as_yaml(data: Dict[str, Any], indent_level: int = 0, is_array_item: bool = False) -> str:
    """Format a dictionary as YAML with proper indentation."""
    if not data:
        return "{}"
    
    indent = "  " * indent_level
    lines = []
    
    for key, value in data.items():
        if isinstance(value, dict):
            if is_array_item and key == next(iter(data.keys())):
                # First key in array item doesn't need extra indentation
                lines.append(f"{key}: {format_dict_as_yaml(value, indent_level + 1)}")
            else:
                lines.append(f"{indent}{key}:")
                dict_lines = format_dict_as_yaml(value, indent_level + 1).split("\n")
                lines.extend(dict_lines)
        elif isinstance(value, list):
            lines.append(f"{indent}{key}:")
            for item in value:
                if isinstance(item, dict):
                    # Format dict without extra indentation, we'll add it manually
                    item_yaml = format_dict_as_yaml(item, 0)
                    item_lines = item_yaml.split("\n")
                    if item_lines:
                        # First line gets the "- " prefix at the correct indent
                        first_line = item_lines[0]
                        lines.append(f"{indent}  - {first_line}")
                        # Subsequent lines get array item indentation  
                        for line in item_lines[1:]:
                            lines.append(f"{indent}    {line}")
                else:
                    lines.append(f"{indent}  - {format_yaml_value(item, 0)}")
        else:
            formatted_value = format_yaml_value(value)
            if is_array_item and key == next(iter(data.keys())):
                # First key in array item doesn't need extra indentation  
                lines.append(f"{key}: {formatted_value}")
            else:
                lines.append(f"{indent}{key}: {formatted_value}")
    
    return "\n".join(lines)