#!/bin/bash

# Helper script to regenerate the DBT project component schema file
# This uses the dg CLI to inspect the component and extract its JSON schema

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Regenerating DBT project component schema..."
echo "Using command: dg utils inspect-component dagster_dbt.DbtProjectComponent --component-schema"

# Change to the repo root and run the command
cd "${SCRIPT_DIR}/../../../../../../.."

# Generate the schema and save it to the file
dg utils inspect-component dagster_dbt.DbtProjectComponent --component-schema > "${SCRIPT_DIR}/schema.json"

echo "Schema file regenerated at: ${SCRIPT_DIR}/schema.json"

# Generate the expected YAML template output
echo "Generating expected YAML template output..."
cd "${SCRIPT_DIR}/../../../.."
python -c "
from dagster_dg_core.yaml_template.converter import YamlTemplate
import json

with open('${SCRIPT_DIR}/schema.json', 'r') as f:
    schema = json.load(f)

template = YamlTemplate.from_json_schema(schema)
with open('${SCRIPT_DIR}/expected_output.yaml', 'w') as f:
    f.write(template.to_string())
"

echo "Expected output file regenerated at: ${SCRIPT_DIR}/expected_output.yaml"
echo "Done!"