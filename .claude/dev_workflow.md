# development workflow for claude

## Use Ruff

**CRITICAL**: After EVERY Python file edit (Write, Edit, MultiEdit), Claude MUST immediately:

1. **Run ruff formatting/linting from git repository root directory**:

   ```bash
   make ruff
   ```

   MUST do after _every_ edit of a Python file.

2. **Fix any remaining issues**: If ruff reports errors that were not automatically fixed, Claude must manually correct them to the best of its ability

3. **Verify success**: Ensure `make ruff` passes cleanly before considering the task complete.

### Style guidelines

- **Formats code** using ruff formatter (replaces black)
- **Sorts imports** combine imports, absolute imports only
- **Enforces** 100-character line limit and other style rules

### common manual fixes needed

When ruff cannot auto-fix issues, Claude should address:

- **Line length violations**: Break long lines appropriately
- **Import organization**: Fix complex import sorting issues
- **Type hints**: Add missing type annotations
- **Docstring formatting**: Ensure proper Google-style docstrings
- **Unused imports/variables**: Remove or fix usage

### example workflow

```bash
# After editing any Python files from repository root:
make ruff

# If errors remain:
# 1. Read the error messages
# 2. Make necessary manual corrections
# 3. Run make ruff again
# 4. Repeat until clean
```

## Use Pytest

- Always run pytest from the repository root and with the full path to the file being tested.
