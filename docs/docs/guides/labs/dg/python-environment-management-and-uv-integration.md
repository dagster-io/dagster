---
title: 'Python environment management and `uv` integration'
sidebar_position: 500
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

:::note

We are working on streamlining the configuration of the `uv` integration, and it
is likely to change in the next few releases.

:::

Many `dg` commands need to spawn subprocesses. For example, when you run `dg list plugins` in a project directory, `dg` does not perform an in-process inspection of the environment in which `dg` itself is running. Instead, it resolves a Python environment for the in-scope project and spawns a subprocess using the `dagster-components` executable (an internal API) in that environment. The output you see on the command line represents the plugins available in the resolved environment, which is not necessarily the same as the environment in which `dg` itself is running.

The Python environment used for a project is determined by the `tool.dg.project.python_environment` setting in the project `pyproject.toml` file. This setting is either:

- `active` (the default), which means that `dg` will use the currently active Python environment.
- `persistent_uv` (not default, but set in dg-scaffolded projects by default), which means that `dg` will use a dedicated Python environment found in `<project_root>/.venv` that is created and managed by `uv`.

If the setting is `active`, then `dg` does nothing fancy. It is up to the user to manage their own Python environments. If individual project-scoped environments are desired, the user must create them, and ensure the appropriate one is activated when running `dg` commands against that project.

If the setting is `persistent_uv`, then `dg` will ignore any activated virtual environments. Subprocesses will be launched using `uv run`, which handles resolution of the project-scoped `.venv` environment and ensures subprocesses are launched in that environment. It also ensures that the environment is up to date with the project's specified dependencies before launching a subprocess.

The `persistent_uv` setting is intended to ease development friction by removing the burden of juggling virtual environments from the user. It is our recommended configuration. However, we are still developing its functionality, and some users may prefer to totally opt out of any environment management "magic". These users should make sure all their projects use `tool.dg.project.python_environment = "active"`.

:::info

Disabling `uv` integration by setting `tool.dg.project.python_environment
= "active"` will currently disable the `dg cache`. This will make some
operations noticeably slower.

:::
