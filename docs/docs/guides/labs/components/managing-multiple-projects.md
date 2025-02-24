---
title: 'Managing multiple projects with Components'
sidebar_position: 40
---

:::info

This feature is still in development and might change in patch releases. It’s not production-ready, and the documentation may also evolve. Stay tuned for updates.

:::

You can use a _workspace_ directory to manage multiple projects within a single coherent directory structure.

A workspace directory contains a root `pyproject.toml` containing workspace-level settings and a `projects` directory containing one or more projects. A workspace does _not_ define a Python environment by default. Instead, Python environments are defined per project.

## Scaffold a new workspace

To scaffold a new workspace with an initial project called `project-1`, run:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/workspace/1-dg-init.txt" />

This will create a new directory called `workspace`, as well a new directory `project-1` within the `projects` folder. It will also setup a new uv-managed Python environment for the project. Let's look at the structure:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/workspace/2-tree.txt" />

Importantly, the `pyproject.toml` file for the `workspace` folder contains an `is_workspace` setting marking this directory as a workspace:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/workspace/3-pyproject.toml" language="TOML" title="workspace/pyproject.toml" />

:::note

`project-1` also contains a virtual environment directory `.venv` that is not shown above. This environment is managed by `uv` and its contents are specified in the `uv.lock` file.

:::

The `project-1` directory contains a `pyproject.toml` file that defines
it as a Dagster project:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/workspace/4-project-pyproject.toml" language="TOML" title="workspace/projects/project-1/pyproject.toml" />

Let's enter this directory and search for registered component types:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/workspace/5-component-type-list.txt"  />

This is the default set of component types available in every new project. We can add to it by installing `dagster-components[sling]`:

<CliInvocationExample contents="uv add 'dagster-components[sling]'" />

:::note

Due to a bug in `sling` package metadata, if you are on a macOS machine with Apple Silicon you may also need to run `uv add sling_mac_arm64`.

:::

And now we have a new available component:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/workspace/6-component-type-list.txt"  />

## Add a second project to the workspace

As stated above, environments are scoped per project.  `dg` commands will only use the environment of `project-1` when we are inside the `project-1` directory.

Let's create another project to demonstrate this:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/workspace/7-scaffold-project.txt"  />

Now we have two projects. We can list them with:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/workspace/8-project-list.txt"  />

And finally, let's check the available component types in `project-2`:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/workspace/9-component-type-list.txt"  />


As you can see, we are back to only the default list of component types. This is because we are now using the environment of `project-2`, in which we have not installed `dagster-components[sling]`.

## Load workspace with dg

For a final step, let's load up our two projects with `dg dev`. `dg dev` will automatically recognize the projects in your workspace and launch them in their respective environments. Let's run `dg dev` back in the
workspace root directory and load up the Dagster UI in your browser:

<CliInvocationExample contents="cd ../.. && dg dev" />

![](/images/guides/build/projects-and-components/setting-up-a-workspace/two-projects.png)
