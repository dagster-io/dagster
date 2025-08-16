# Plan: Fix Union Type Handling in Schema Generation

## Problem Analysis
The current schema generation relies on Pydantic's automatic schema generation instead of explicitly processing resolver annotations. While it works for simple cases like `partitions_def`, this approach:
- Lacks explicit control over union type representation  
- Doesn't follow a consistent pattern for extracting schema info from resolvers
- May miss complex union cases where `model_field_type` differs from Pydantic's inference

## Implementation Plan

### Phase 1: Create Union Type Extraction Utility
1. **Add utility function** to extract union types from resolver annotations:
   ```python
   def _extract_union_schema_from_resolver(field_annotation) -> Optional[dict]:
       # Extract Union from Annotated[T, Resolver(..., model_field_type=Union[...])]
       # Generate proper anyOf schema from union members
   ```

2. **Handle different union patterns**:
   - Direct union of Pydantic models: `Union[ModelA, ModelB]`
   - Mixed unions with primitives: `Union[ModelA, str]`
   - Nested unions and optional types

### Phase 2: Integrate Union Processing
1. **Update `_generate_defs_yaml_schema()`** to check for resolver unions:
   - Scan `AssetsDefUpdateKwargs.model()` field annotations
   - Extract resolver `model_field_type` information  
   - Override auto-generated schemas with explicit union schemas

2. **Preserve existing functionality**:
   - Keep current schema generation as fallback
   - Only override when resolver unions are detected
   - Maintain all existing `$defs` references

### Phase 3: Add Missing Union Fields
1. **Investigate missing fields** like `backfill_policy`:
   - Check if they should be in `AssetsDefUpdateKwargs`
   - Add them if they're missing from asset attributes
   - Ensure proper union schema generation

### Phase 4: Testing & Validation
1. **Add comprehensive tests** for union type validation:
   - Test all partition definition types
   - Test mixed union types (model + primitive)
   - Test nested union structures
   - Verify schema completeness and correctness

2. **Integration testing**:
   - Test CLI `--defs-yaml-schema` output
   - Validate against real component YAML files
   - Ensure IntelliSense/validation works correctly

## Expected Outcomes
- ✅ Explicit, consistent union type handling
- ✅ Better control over schema representation
- ✅ Foundation for handling complex future union cases
- ✅ More robust schema generation architecture

## Current State Analysis

### What Works
1. **Union validation works correctly** - The `partitions_def` field properly validates union types like `{type: 'daily', start_date: '2023-01-01'}`
2. **Schema generation works correctly** - The generated JSON schema includes proper `anyOf` structures with references to all partition definition models
3. **All partition models are included** - The `$defs` section contains all the partition definition models

### The Real Issue
The issue is **architectural**: we're relying on Pydantic's automatic schema generation instead of explicitly processing the resolver's `model_field_type` information. This could lead to problems when:

1. **Complex Union Types**: Where the resolver's `model_field_type` Union doesn't match what Pydantic infers
2. **Future Schema Evolution**: If we need more control over how union types are represented
3. **Consistency**: We should be using the same pattern throughout - extracting schema info from resolver annotations

### Examples of Resolver Union Types Found

1. **partitions_def** in `SharedAssetKwargs`:
   ```python
   partitions_def: Annotated[
       Optional[PartitionsDefinition],
       Resolver(
           resolve_partitions_def,
           description="The partitions definition for the asset.",
           model_field_type=Union[
               HourlyPartitionsDefinitionModel,
               DailyPartitionsDefinitionModel,
               WeeklyPartitionsDefinitionModel,
               TimeWindowPartitionsDefinitionModel,
               StaticPartitionsDefinitionModel,
           ],
       ),
   ] = None
   ```

2. **backfill_policy** in `OpSpec` (not currently in AssetsDefUpdateKwargs):
   ```python
   backfill_policy: Annotated[
       Optional[BackfillPolicy],
       Resolver(
           resolve_backfill_policy,
           model_field_type=Union[SingleRunBackfillPolicyModel, MultiRunBackfillPolicyModel],
       ),
   ] = None
   ```

## Navigation Notes: Resolver System

Based on analysis of the codebase, here are key patterns for navigating the resolved system:

### Finding Union Types in Resolvers
- Look for `Annotated[T, Resolver(..., model_field_type=Union[...])]` patterns
- The `model_field_type` parameter contains the actual schema-generation model
- Union members are typically Resolvable Model classes

### Accessing Resolver Information
- Runtime type: What the field contains at runtime (e.g., `Optional[PartitionsDefinition]`)
- `model_field_type`: What should be used for schema generation (e.g., `Union[HourlyPartitionsDefinitionModel, ...]`)
- Access via: `field_annotation.__metadata__[0].model_field_type` where the annotation is `Annotated`

### Schema Generation Strategy
- Use `SomeResolvableClass.model().model_json_schema()` for automatic generation
- Extract union info from resolver annotations for explicit control
- Manually compose complex schemas when automatic generation fails