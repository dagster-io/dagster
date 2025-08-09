# Dead Code Removal #002: asset_post_processors Deprecated Fields

## Summary
Removed the deprecated `asset_post_processors` fields from both `AirflowInstanceComponent` and `SlingReplicationCollectionComponent` that were past their deletion deadline and already non-functional.

## Change Details
- **Files Modified**: 3 files across 2 components
- **Lines Removed**: ~40 lines total (field declarations, deprecation checks, tests, imports)
- **Field Signature**: `asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None`

## Analysis Performed
1. **Deadline Check**: Fields were marked for deletion on 2025-06-10, now past deadline (2025-08-08)
2. **Functionality Check**: Fields already threw exceptions when used - completely non-functional
3. **Usage Analysis**: Only test specifically validated the deprecation error
4. **Migration Path**: Clear migration guidance was provided in the error messages

## Components Modified

### 1. AirflowInstanceComponent
**File**: `python_modules/libraries/dagster-airlift/dagster_airlift/core/components/airflow_instance/component.py`
- Removed field declaration with TODO comment
- Removed deprecation check in `build_defs()` method
- Removed `AssetPostProcessor` import (now unused)

### 2. SlingReplicationCollectionComponent 
**File**: `python_modules/libraries/dagster-sling/dagster_sling/components/sling_replication_collection/component.py`
- Removed field declaration with TODO comment  
- Removed deprecation check in `build_defs()` method
- Removed `AssetPostProcessor` import (now unused)

### 3. Test Cleanup
**File**: `python_modules/libraries/dagster-sling/dagster_sling_tests/test_sling_replication_collection_component.py`
- Removed `test_asset_post_processors_deprecation_error()` test function
- Test was validating the deprecation error that no longer applies

## Original Deprecation Context
Both fields were deprecated in favor of the new `post_processing` configuration:

**Old (Deprecated)**:
```yaml
type: dagster_sling.SlingReplicationCollectionComponent
attributes:
  asset_post_processors:
    - target: "*"
      attributes:
        group_name: "my_group"
```

**New (Recommended)**:
```yaml
type: dagster_sling.SlingReplicationCollectionComponent  
attributes: ~
post_processing:
  assets:
    - target: "*"
      attributes:
        group_name: "my_group"
```

## Risk Assessment
**Risk Level: MINIMAL**
- Fields were already completely non-functional (threw exceptions)
- Past their official deletion deadline by ~2 months  
- Clear migration path provided and documented
- No breaking changes to functional APIs
- Components work exactly the same without these fields

## Testing Performed
✅ **Linting**: `make ruff` passed successfully (3 import cleanups)  
✅ **Sling Component Tests**: All 27 tests passed  
✅ **Airlift Component Tests**: 6 passed, 1 skipped (unrelated)  
✅ **No Regression**: All existing functionality preserved  

## Files Changed
```
python_modules/libraries/dagster-airlift/dagster_airlift/core/components/airflow_instance/component.py
    - Removed asset_post_processors field declaration and TODO comment (line 200-201)
    - Removed deprecation check in build_defs method (18 lines)
    - Removed AssetPostProcessor import (line 18)

python_modules/libraries/dagster-sling/dagster_sling/components/sling_replication_collection/component.py
    - Removed asset_post_processors field declaration and TODO comment (line 142-143)
    - Removed deprecation check in build_defs method (18 lines)  
    - Removed AssetPostProcessor import (line 21)

python_modules/libraries/dagster-sling/dagster_sling_tests/test_sling_replication_collection_component.py
    - Removed test_asset_post_processors_deprecation_error function (29 lines)
```

## Impact
- **Positive**: Removed ~40 lines of dead/deprecated code
- **Positive**: Eliminated TODO technical debt past deadline
- **Positive**: Simplified component APIs by removing non-functional fields
- **Positive**: Improved user experience (no more confusing deprecated options)
- **Negative**: None - fields were already completely broken

## Migration Impact
Since the fields already threw exceptions when used, no existing working configurations are affected. Any users who had the deprecated fields in their YAML configurations would have already been receiving clear error messages with migration instructions.

## Next Steps
This removal demonstrates successful cleanup of deprecated code with clear deadlines. The approach can be applied to other deprecated features following similar patterns.