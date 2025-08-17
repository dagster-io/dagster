# Generic Union Type Support in Schema Generation

## Current Problem
The YAML template generator doesn't properly handle Union types (represented as `anyOf` with multiple `$ref` objects in JSON schema). This affects not just `partitions_def` but any field with Union types like `backfill_policy`, and potentially others.

## Generic Solution Approach

### Phase 1: Enhance Union Type Detection
- **File**: `yaml_template_generator.py`
- **Function**: `_add_field_lines()`
- **Goal**: Detect when `anyOf` contains multiple `$ref` objects (indicating a Union type)
- **Logic**: 
  ```python
  # Detect Union types with multiple $ref objects
  refs = [opt for opt in field_schema["anyOf"] if "$ref" in opt]
  if len(refs) > 1:
      # Handle as Union type with multiple options
  ```

### Phase 2: Generate Multi-Option Templates  
- **Goal**: Create templates showing all Union type options with clear commenting
- **Approach**:
  - For each `$ref` in the `anyOf`, resolve the schema and generate its template
  - Present all options as commented alternatives in YAML
  - Include the discriminator field (usually `type`) to show how to choose between options

### Phase 3: Improve Example Generation
- **Function**: `_get_example_value()`
- **Goal**: For Union types, pick the first non-string option and generate a complete example
- **Current behavior**: Already prioritizes non-string types, but needs enhancement for better Union handling

### Phase 4: Enhanced Template Structure
- **Goal**: Generate clear, comprehensive templates for any Union type field
- **Example Output**:
  ```yaml
  partitions_def:  # Optional: Choose one of the following types:
    # Option 1 - Hourly partitions:
    # type: hourly
    # start_date: "2024-01-01T00:00:00"
    # timezone: "UTC"
    # minute_offset: 0
    
    # Option 2 - Daily partitions:
    # type: daily
    # start_date: "2024-01-01"
    # timezone: "UTC"
    # minute_offset: 0
    # hour_offset: 0
    
    # Option 3 - Static partitions:
    # type: static  
    # partition_keys: ["partition1", "partition2"]
    
    # ... etc
  ```

## Benefits
- **Generic**: Works for any Union type field (backfill_policy, partitions_def, etc.)
- **Comprehensive**: Shows all available options with their specific schemas
- **User-friendly**: Clear documentation and examples for each option
- **Future-proof**: Automatically handles new Union types as they're added

## Implementation Strategy
1. Enhance `anyOf` handling to detect Union types
2. Create a generic Union template generator
3. Apply to all fields with Union types, not just partitions
4. Maintain backward compatibility with existing non-Union anyOf handling

## Files to Modify
- `python_modules/libraries/dagster-dg-cli/dagster_dg_cli/utils/yaml_template_generator.py`

## Test Data Location
- `python_modules/libraries/dagster-dg-core/dagster_dg_core_tests/yaml_template/test_data/python_script/`