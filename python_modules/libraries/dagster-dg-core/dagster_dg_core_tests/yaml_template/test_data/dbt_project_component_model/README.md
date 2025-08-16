# DBT Project Component Model Test Data

This directory contains test data for validating the YAML template conversion of complex JSON schemas.

## Files

- **`schema.json`**: The JSON schema for the DbtProjectComponentModel, extracted from the Dagster DBT component
- **`expected_output.yaml`**: The expected YAML template output when processing the schema through the converter
- **`regenerate_schema.sh`**: Helper script to regenerate the schema file using the `dg` CLI command
- **`README.md`**: This documentation file

## Usage

### Regenerating the Schema

If the DbtProjectComponent schema changes, you can regenerate the schema file by running:

```bash
./regenerate_schema.sh
```

This will use the command:

```bash
dg utils inspect-component dagster_dbt.DbtProjectComponent --component-schema
```

### Updating Expected Output

After regenerating the schema, you may need to update the expected output by running:

```bash
python -c "
import json
from dagster_dg_core.yaml_template.converter import YamlTemplate

with open('schema.json', 'r') as f:
    schema = json.load(f)

template = YamlTemplate.from_json_schema(schema)
result = template.to_string()

with open('expected_output.yaml', 'w') as f:
    f.write(result)
"
```

## Test Purpose

This test validates that the YAML template converter can handle complex, real-world JSON schemas with:

- Nested object definitions (`$defs`)
- Schema references (`$ref`)
- Multiple type unions (`anyOf`)
- Complex nested structures
- Arrays of objects
- Various constraint types

The test ensures that the converter gracefully handles unsupported JSON Schema features while still generating useful YAML templates for LLM consumption.
