---
title: 'Creating a project with components'
sidebar_position: 100
---

:::info

This feature is still in development and might change in patch releases. It’s not production ready, and the documentation may also evolve. Stay tuned for updates.

:::

:::note Prerequisites

Before creating a project with components, you must follow the [steps to install `uv` and `dg`](/guides/labs/components/index.md#installation).

:::

After [installing dependencies](/guides/labs/components/index.md#installation), you can scaffold a components-ready project. In the example below, we scaffold a project called `jaffle-platform`:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/2-scaffold.txt"  />

This command builds a project and initializes a new Python virtual environment inside of it. When using `dg`'s default environment management behavior, you won't need to worry about activating this virtual environment yourself.

:::note

For more information about the files, directories, and default configuration in a components project, see "[Files and directories in a components project](files-and-directories-in-a-components-project)".

:::

## Next steps

After scaffolding your project with components, you can [add more components](adding-components) to complete your pipeline.