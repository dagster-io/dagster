# Dead Code Removal #6: Expired Hidden Parameter

## Summary
Removed the expired `@hidden_param` decorator for the `auto_materialize_policy` parameter in `AssetSpec`. This parameter was deprecated with `breaking_version="1.10.0"` but the current Dagster version is 1.11.5, making it past its expiration date.

## Parameter Removed
```python
@hidden_param(
    param="auto_materialize_policy",
    breaking_version="1.10.0",
    additional_warn_text="use `automation_condition` instead",
)
```

Applied to the `AssetSpec` class in `python_modules/dagster/dagster/_core/definitions/assets/definition/asset_spec.py`.

## Location & Context
- **File**: `python_modules/dagster/dagster/_core/definitions/assets/definition/asset_spec.py`
- **Class**: `AssetSpec`
- **Deprecation Date**: Version 1.10.0
- **Current Version**: 1.11.5
- **Migration Path**: Use `automation_condition` parameter instead

## Replacement Pattern
**Before (deprecated usage):**
```python
AssetSpec(key="my_asset", auto_materialize_policy=AutoMaterializePolicy.eager())
```

**After (current usage):**
```python
AssetSpec(key="my_asset", automation_condition=AutomationCondition.eager())
```

## Files Modified
1. **Core Class**: `python_modules/dagster/dagster/_core/definitions/assets/definition/asset_spec.py` - Removed `@hidden_param` decorator
2. **Test Update**: `python_modules/dagster/dagster_tests/definitions_tests/test_asset_spec.py` - Updated `test_resolve_automation_condition()` to remove deprecated parameter usage

## Analysis Process
1. **Search**: Found all deprecated features with `breaking_version="1.10.0"`
2. **Selection**: Chose `@hidden_param` decorator as a good candidate (clean removal)
3. **Verification**: Confirmed parameter is properly rejected after removal
4. **Testing**: Updated test to remove deprecated usage patterns
5. **Validation**: Ensured all tests pass and linting is clean

## Verification
- **Parameter Rejection**: `AssetSpec(key='test', auto_materialize_policy=None)` now raises `TypeError: AssetSpec got an unexpected keyword argument 'auto_materialize_policy'`
- **Normal Usage**: `AssetSpec(key='test')` works correctly
- **Migration Path**: `AssetSpec(key='test', automation_condition=AutomationCondition.eager())` works correctly
- **Tests**: All AssetSpec tests pass (24 passed, 1 updated)
- **Linting**: Code passes all style checks

## Impact
- **Parameter Cleanup**: Removes deprecated parameter that should have been removed in 1.10.0
- **Clear Migration**: Users must now use the recommended `automation_condition` parameter
- **Test Modernization**: Updates test code to use current API patterns
- **No Silent Failures**: Attempts to use deprecated parameter now fail fast with clear error message

## Breaking Change Confirmation
This is an expected breaking change since:
- The parameter was marked for removal in version 1.10.0
- We are currently at version 1.11.5 (1.5 versions past expiration)
- The replacement (`automation_condition`) has been available throughout this period
- The parameter was hidden (not part of normal public API documentation)

## Files Created
- `dead_code_removal_6_expired_hidden_param.md`: This documentation
- `dead_code_removal_6_expired_hidden_param.patch`: Git patch of all changes

This removal represents proper deprecation lifecycle management by removing parameters at their scheduled removal version, while ensuring tests and documentation are updated accordingly.