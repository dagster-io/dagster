# Exclude Lists Management

## Overview

Exclude lists enable incremental migration by temporarily allowing known violations while preventing new ones. They're defined in `exclude_lists.py`.

## Types of Exclude Lists

- **EXCLUDE_MISSING_RST**: `@public` symbols without RST documentation
- **EXCLUDE_MISSING_PUBLIC**: RST symbols without `@public` decorators
- **EXCLUDE_MISSING_EXPORT**: `@public` symbols not exported at top-level
- **EXCLUDE_MODULES_FROM_PUBLIC_SCAN**: Modules to skip during scanning
- **EXCLUDE_RST_FILES**: RST files to skip during symbol extraction

## Key Commands

```bash
# Audit exclude lists to find entries that can be removed
dagster-docs check exclude-lists --missing-public --missing-rst --missing-export

# Check current validation state
dagster-docs check exports --all
```

## Best Practices

1. **Add entries sparingly** - Only when necessary for incremental migration
2. **Remove promptly** - Clean up entries as soon as issues are resolved
3. **Document reasons** - Add comments explaining why entries are excluded
4. **Regular audits** - Schedule weekly exclude list cleanup

## Entry Format

Use dotted symbol paths:

```python
# GOOD
"dagster.asset"                    # Top-level export
"dagster_aws.pipes.PipesECSClient" # Library symbol

# BAD
"/path/to/file.py"                # Don't use file paths
"asset"                           # Need full module path
```

## Migration Workflow

1. Add `@public` decorator to symbol
2. Add to appropriate exclude list if not ready for full compliance
3. Create RST documentation and top-level export
4. Remove from exclude list

Regular auditing ensures continuous progress toward full compliance.
