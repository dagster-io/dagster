#!/usr/bin/env python3

import re

# Read the test file
with open("dagster_dg_core_tests/yaml_template/test_converter.py") as f:
    content = f.read()

# Define replacement patterns
replacements = [
    # Type format changes
    (r": string  # Optional", ": <string>  # OPTIONAL"),
    (r": string  # Required", ": <string>  # REQUIRED"),
    (r": integer  # Optional", ": <integer>  # OPTIONAL"),
    (r": integer  # Required", ": <integer>  # REQUIRED"),
    (r": number  # Optional", ": <number>  # OPTIONAL"),
    (r": number  # Required", ": <number>  # REQUIRED"),
    (r": boolean  # Optional", ": <boolean>  # OPTIONAL"),
    (r": boolean  # Required", ": <boolean>  # REQUIRED"),
    (r": null  # Optional", ": <null>  # OPTIONAL"),
    (r": null  # Required", ": <null>  # REQUIRED"),
    # Type format changes with constraints
    (r": string  # Optional:", ": <string>  # OPTIONAL:"),
    (r": string  # Required:", ": <string>  # REQUIRED:"),
    (r": integer  # Optional:", ": <integer>  # OPTIONAL:"),
    (r": integer  # Required:", ": <integer>  # REQUIRED:"),
    (r": number  # Optional:", ": <number>  # OPTIONAL:"),
    (r": number  # Required:", ": <number>  # REQUIRED:"),
    # Array type changes
    (r"  - string", "  - <string>"),
    (r"  - integer", "  - <integer>"),
    (r"  - number", "  - <number>"),
    (r"  - boolean", "  - <boolean>"),
    # Object descriptions
    (r"  # Optional:", "  # OPTIONAL:"),
    (r"  # Required:", "  # REQUIRED:"),
    # Specific example value changes
    (r'name: "Jane Doe"', 'name: "example_string"'),
    (r"age: 30", "age: 42"),
    (r'street: "123 Main St"', 'street: "example_string"'),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Write back the updated content
with open("dagster_dg_core_tests/yaml_template/test_converter.py", "w") as f:
    f.write(content)

# Updated test file with new format
