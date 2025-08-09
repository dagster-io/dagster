# Dead Code Removal #4: all_none Function

## Summary
Removed the unused `all_none` function from `python_modules/dagster/dagster/_utils/__init__.py`. This function was defined but never used anywhere in the codebase.

## Function Removed
```python
def all_none(kwargs: Mapping[object, object]) -> bool:
    for value in kwargs.values():
        if value is not None:
            return False
    return True
```

## Location
- **File**: `python_modules/dagster/dagster/_utils/__init__.py`
- **Lines**: 233-237
- **Size**: 5 lines

## Analysis Process
1. **Search for function calls**: Searched entire codebase for calls to `all_none()` - no matches found
2. **Search for imports**: Searched for any imports of `all_none` - no matches found  
3. **Public API check**: Function was not listed in any `__all__` declarations
4. **Usage verification**: Function was only defined but never called anywhere

## Verification
- **Tests**: All utils tests continue to pass (72 passed, 1 skipped)
- **Linting**: Code formatting and style checks pass
- **No breaking changes**: Function was purely internal and unused

## Impact
- **Codebase cleanup**: Removes 5 lines of truly dead code
- **Maintenance benefit**: Eliminates unused function that could confuse developers
- **No functional impact**: Function was never called, so removal has no behavioral effect

## Files Modified
- `python_modules/dagster/dagster/_utils/__init__.py`: Removed unused `all_none` function

This removal continues the systematic dead code cleanup effort, targeting utility functions that are defined but never used.