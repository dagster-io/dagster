---
name: dignified-python
description: Python coding standards with automatic version detection.
  Use when writing, reviewing, or refactoring Python to ensure adherence to LBYL exception
  handling patterns, modern type syntax (list[str], str | None), pathlib operations,
  ABC-based interfaces, absolute imports, and explicit error boundaries at CLI level.
  Also provides production-tested code smell patterns from Dagster Labs for API design,
  parameter complexity, and code organization. Essential for maintaining erk's dignified
  Python standards.
---

# Dignified Python Coding Standards

## Core Knowledge (ALWAYS Loaded)

@dignified-python-core.md

## Version Detection

**Identify the project's minimum Python version** by checking (in order):

1. `pyproject.toml` - Look for `requires-python` field (e.g., `requires-python = ">=3.12"`)
2. `setup.py` or `setup.cfg` - Look for `python_requires`
3. `.python-version` file - Contains version like `3.12` or `3.12.0`
4. Default to Python 3.12 if no version specifier found

**Once identified, load the appropriate version-specific file:**

- Python 3.10: Load `versions/python-3.10.md`
- Python 3.11: Load `versions/python-3.11.md`
- Python 3.12: Load `versions/python-3.12.md`
- Python 3.13: Load `versions/python-3.13.md`

## Conditional Loading (Load Based on Task Patterns)

Core files above cover 80%+ of Python code patterns. Only load these additional files when you detect specific patterns:

Pattern detection examples:

- If task mentions "click" or "CLI" -> Load `cli-patterns.md`
- If task mentions "subprocess" -> Load `subprocess.md`

## How to Use This Skill

1. **Core knowledge** is loaded automatically (LBYL, pathlib, ABC, imports, exceptions)
2. **Version detection** happens once - identify the minimum Python version and load the appropriate version file
3. **Additional patterns** may require extra loading (CLI patterns, subprocess)
4. **Each file is self-contained** with complete guidance for its domain
