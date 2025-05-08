---
title: 'Managing multiple projects with dg'
sidebar_label: 'Managing multiple projects'
sidebar_position: 300
description: Manage multiple isolated Dagster projects using dg, each with unique environments, by creating a workspace directory with dg scaffold project.
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

:::note

If you're just getting started, we recommend [scaffolding a single project](/guides/labs/dg/creating-a-project) instead of a workspace with multiple projects.

:::

If you need to collaborate with multiple teams, or work with conflicting dependencies that require isolation from each other, you can scaffold a workspace directory that contains multiple projects, each with their own separate Python environment.

A workspace directory contains a root `dg.toml` with workspace-level settings, and a `projects` directory with one or more projects.

:::note

A workspace does not define a Python environment by default. Instead, Python environments are defined per project.

:::

## Scaffold a new workspace and first project

To scaffold a new workspace called `dagster-workspace`, run `dg scaffold
workspace`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/1-dg-scaffold-workspace.txt" />

Now we'll create a project inside our workspace called `project-1`. Run `dg scaffold project` with the `--python-environment uv_managed` option. You will be prompted for the name of the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/2-dg-scaffold-project.txt" />

:::note

Currently `dg` workspaces only support projects using `uv` with `project.python_environment.uv_managed = true`. This means that the Python environment for the workspace is managed by `uv`, and subprocesses are launched by `uv run`, ignoring the activated virtual environment. If all projects in a workspace do not conform to this, you will likely encounter errors.

:::

This will create a new directory called `dagster-workspace` with a `projects` subdirectory that contains `project-1`. It will also set up a new `uv`-managed Python environment for this project.

### Review workspace structure

The new workspace has the following structure:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/3-tree.txt" />

The `dg.toml` file for the `dagster-workspace` folder contains a `directory_type = "workspace"` setting that marks this directory as a workspace:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/workspace/4-dg.toml"
  language="TOML"
  title="dagster-workspace/dg.toml"
/>

:::note

`project-1` also contains a virtual environment directory called `.venv` that is not shown above. This environment is managed by `uv` and its contents are specified in the `uv.lock` file.

:::

The `project-1` directory contains a `pyproject.toml` file with a
`tool.dg.directory_type = "project"` section that defines it as a `dg` project:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/workspace/5-project-pyproject.toml"
  language="TOML"
  title="dagster-workspace/projects/project-1/pyproject.toml"
/>

## Add a second project to the workspace

As noted above, environments are scoped per project. `dg` commands will only use the environment of `project-1` when you are inside the `project-1` directory.

Let's create another project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/6-scaffold-project.txt" />

Now we have two projects. We can list them with:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/7-project-list.txt" />

## Load workspace with `dg`

Finally, let's load up our two projects with `dg dev`. `dg dev` will automatically recognize the projects in your workspace and launch them in their respective environments. Let's run `dg dev` back in the workspace root directory and load up the Dagster UI in a browser:

<CliInvocationExample contents="cd ../.. && dg dev" />

![](/images/guides/build/projects-and-components/setting-up-a-workspace/two-projects.png)
