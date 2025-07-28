# Validate Changed Docstrings

Validates Python docstrings in all uncommitted changed files using Sphinx parsing.

This command finds files with uncommitted changes (staged or unstaged), extracts Python symbols with docstrings, and validates them using the existing docstring validation tool to catch RST syntax errors and other docstring issues early in development.

## Usage

Run the validation script on changed files:

```bash
dagster-docs check docstrings --changed
```

## What it does

1. Uses `git diff --name-only HEAD` to find uncommitted Python files
2. Parses each file's AST to extract classes, functions, and methods with docstrings
3. Validates each symbol's docstring using the Sphinx parsing pipeline
4. Reports errors and warnings with clear symbol paths
5. Returns non-zero exit code if any errors are found

## Example output

```
Found 2 uncommitted Python files:
  python_modules/dagster/dagster/_core/definitions/decorators/asset_decorator.py
  python_modules/dagster/dagster/_core/definitions/asset.py

Validating 8 symbols with docstrings...

--- dagster._core.definitions.decorators.asset_decorator.asset ---
  ERROR: RST syntax: <string>:111: (WARNING/2) Cannot analyze code. No Pygments lexer found for "pythonkjdfkd".

Summary: 1 errors, 0 warnings
✗ Some docstring validations failed
```

This helps catch docstring issues before they reach the documentation build process.
