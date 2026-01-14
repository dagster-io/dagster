---
title: 'Troubleshooting components'
description: How to troubleshoot components.
sidebar_position: 500
unlisted: true
---

This page lists common checks when a component fails to load or behaves unexpectedly.

## Quick checks

- **Validate the component type string**. Ensure the type name matches the registered component class and that the package providing it is installed in your environment.
- **Confirm configuration fields**. Component configuration is validated on load. If a field is missing or mis-typed, the error message will include the field path to update.
- **Verify workspace paths**. If you are using a workspace, confirm that `dg.toml` points at the correct project directories and that the project loads on its own.

## Inspecting load errors

If a component fails to load, the code location will show a load error in the UI and in CLI output. Use the stack trace there to locate the file and configuration entry that caused the failure.

## Next steps

For a refresher on how components are structured, see the [components overview](/guides/build/components).
