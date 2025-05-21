---
description: Python environment management and uv integration with dg.
sidebar_position: 550
title: Python environment management and uv integration
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

:::note

We are working on streamlining the configuration of the `uv` integration, and it
is likely to change in the next few releases.

:::

Many `dg` commands need to spawn subprocesses. For example, when you run `dg list plugins` in a project directory, `dg` does not perform an in-process inspection of the environment in which `dg` itself is running. Instead, it resolves a Python environment for the in-scope project and spawns a subprocess using the `dagster-components` executable (an internal API) in that environment. The output you see on the command line represents the plugins available in the resolved environment, which is not necessarily the same as the environment in which `dg` itself is running.

The Python environment used for a project is determined by the `tool.dg.project.python_environment` setting in the project `pyproject.toml` file. This setting is either `active` (the default) or `uv_managed`:

<Tabs>
  <TabItem value="active" label="active">
    <Tabs>
      <TabItem value="dg.toml" label="dg.toml">
        ``` [project.python_environment] active = true ```
      </TabItem>
      <TabItem value="pyproject.toml" label="pyproject.toml">
        ``` [tool.dg.project.python_environment] active = true ```
      </TabItem>
    </Tabs>
  </TabItem>
  <TabItem value="uv_managed" label="uv_managed">
    <Tabs>
      <TabItem value="dg.toml" label="dg.toml">
        ``` [project.python_environment] uv_managed = true ```
      </TabItem>
      <TabItem value="pyproject.toml" label="pyproject.toml">
        ``` [tool.dg.project.python_environment] uv_managed = true ```
      </TabItem>
    </Tabs>
  </TabItem>
</Tabs>

If the setting is `active` (the default), then it is up to the user to manage their own Python environments. If individual project-scoped environments are desired, the user must create them, and ensure the appropriate one is activated when running `dg` commands against that project. We try to guide users in this direction when they run `dg scaffold project`. After a project is scaffolded by `dg scaffold project`, we prompt the user for permission to automatically run `uv sync`, and recommend they immediately activate the newly created virtual environment.

If the setting is `uv_managed`, then `dg` will ignore any activated virtual environments. Subprocesses will be launched using `uv run`, which handles resolution of the project-scoped `.venv` environment and ensures subprocesses are launched in that environment. It also ensures that the environment is up to date with the project's specified dependencies before launching a subprocess.

The `uv_managed` setting is intended to ease development friction by removing the burden of juggling virtual environments from the user. It is our recommended configuration. However, we are still developing its functionality, and some users may prefer to totally opt out of any environment management "magic". For this reason the default is currently `active`.
