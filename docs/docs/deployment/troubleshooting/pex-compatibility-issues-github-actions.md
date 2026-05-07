---
title: Compatible Python interpreter and wheel dependency errors in GitHub Actions for Dagster+
sidebar_position: 60
description: How to fix PEX and cryptography wheel incompatibilities in GitHub Actions workflows for Dagster+.
---

## Problem description

When using Dagster+ GitHub Actions, you may receive errors about failing to find compatible interpreters or resolve wheel dependencies for various packages. These compatibility issues typically arise when using older Ubuntu versions (like `ubuntu-20.04`), which may not be compatible with the Python executable (PEX) environment used by the Dagster+ GitHub Action.

## Solution

The primary solution for PEX compatibility issues with Dagster+ GitHub Action, particularly around cryptography wheels or other dependencies, is to use a compatible GitHub Actions runner image. Dagster recommends and officially supports the `ubuntu-latest` or `ubuntu-22.04` runners.

To resolve these issues:

1. Update your workflow YAML to use `ubuntu-latest` or `ubuntu-22.04` as the runner.
2. Use Python 3.11 for better wheel compatibility.
3. Add pip caching for improved performance.

```yaml
runs-on: ubuntu-latest
steps:
  - name: Set up Python
    uses: actions/setup-python@v4
    if: steps.prerun.outputs.result != 'skip'
    with:
      python-version: '3.11'
      cache: 'pip'

  - name: Install build dependencies
    if: steps.prerun.outputs.result != 'skip'
    run: |
      python -m pip install --upgrade pip setuptools wheel
      pip install --upgrade cryptography>=3.4.0
      pip install --upgrade PyJWT
```
