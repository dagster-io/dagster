# FivetranAccountComponent Test Data

This directory contains test data for validating the YAML template conversion of the dagster_fivetran.FivetranAccountComponent JSON schema.

## Files

- **`schema.json`**: The JSON schema for the FivetranAccountComponent, extracted using the `dg` CLI command
- **`expected_output.yaml`**: The expected YAML template output when processing the schema through the converter
- **`README.md`**: This documentation file

## Usage

### Regenerating the Schema and Expected Output

To regenerate both the schema and expected output, run from the test_data directory:

```bash
python ../regenerate_schema.py dagster_fivetran.FivetranAccountComponent
```

This will:
1. Use `dg utils inspect-component dagster_fivetran.FivetranAccountComponent --component-schema` to extract the JSON schema
2. Process the schema through the YAML template converter
3. Update both `schema.json` and `expected_output.yaml`

## Test Purpose

This test validates that the YAML template converter can handle the dagster_fivetran.FivetranAccountComponent schema, ensuring proper handling of:

- Complex nested structures
- Schema references (`$ref`) 
- Multiple type unions (`anyOf`)
- Various constraint types
- Arrays and objects

The test ensures the converter generates useful YAML templates for LLM consumption.
