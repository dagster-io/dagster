---
title: 'Creating a library of components'
sidebar_position: 200
---

:::info

This feature is still in development and might change in patch releases. It’s not production ready, and the documentation may also evolve. Stay tuned for updates.

:::

To let the `dg` CLI know that your Python package contains component types, update your `pyproject.toml` file with the following configuration:

```toml
[tool.dg]
is_component_lib = true
```

By default, it is assumed that all component types will be defined in `your_package.lib`. If you'd like to define your components in a different directory, you can specify this in your `pyproject.toml` file:

```toml
[tool.dg]
is_component_lib = true
component_lib_package="your_package.other_module"
```

Once this is done, as long as this package is installed in your environment, you'll be able to use the `dg` command-line utility to interact with your component types.