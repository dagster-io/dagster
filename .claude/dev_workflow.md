# development workflow for claude

## post-edit requirements

After making any Python code changes, Claude must:

1. **Run ruff formatting/linting**:

   ```bash
   make ruff
   ```

2. **Fix any remaining issues**: If ruff reports errors that were not automatically fixed, Claude must manually correct them to the best of its ability

3. **Verify success**: Ensure `make ruff` passes cleanly before considering the task complete

## what make ruff does

- **Formats code** using ruff formatter (replaces black)
- **Sorts imports** according to project standards
- **Lints code** and reports violations
- **Auto-fixes** many issues automatically
- **Enforces** 100-character line limit and other style rules

## common manual fixes needed

When ruff cannot auto-fix issues, Claude should address:

- **Line length violations**: Break long lines appropriately
- **Import organization**: Fix complex import sorting issues
- **Type hints**: Add missing type annotations
- **Docstring formatting**: Ensure proper Google-style docstrings
- **Unused imports/variables**: Remove or fix usage
- **Code complexity**: Refactor overly complex functions

## workflow integration

This process ensures:

- **Consistent code style** across all contributions
- **Clean git history** without formatting noise
- **Adherence** to project standards
- **Immediate feedback** on style violations

## example workflow

```bash
# After editing any Python files:
make ruff

# If errors remain:
# 1. Read the error messages
# 2. Make necessary manual corrections
# 3. Run make ruff again
# 4. Repeat until clean
```

## critical reminder

**Never consider a Python code task complete until `make ruff` passes without errors or warnings.**
