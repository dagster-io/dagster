---
title: 'Creating workspaces to manage multiple projects'
sidebar_position: 1000
description: Manage multiple isolated Dagster projects by creating a workspace directory with the create-dagster command.
---

:::note

If you're just getting started, we recommend [creating a single project](/guides/build/projects/creating-projects) instead of a workspace with multiple projects.

:::

If you need to collaborate with multiple teams, or work with conflicting dependencies that require isolation from each other, you can scaffold a workspace directory that contains multiple projects, each with their own separate Python environment, while still being able to access all of your assets across every project in a single instance of the Dagster UI or `dg` CLI.

A workspace directory contains a root [`dg.toml` file](/guides/build/projects/workspaces/dg-toml) with workspace-level settings, and a `projects` directory with one or more projects. It also contains a Python environment in a `deployments/local` folder that can be used for running `dg` commands locally against the workspace.

When a `dg` command runs in a workspace, it will create a subprocess for each project using that project's virtual environment, and communicate with each process through an API layer. The diagram below demonstrates a workspace with two projects, as well as their virtual environments.

![Diagram showing the virtual environments used by a workspace and 2 projects](/images/guides/build/projects-and-components/setting-up-a-workspace/workspace-venvs.png)

## Creating a new workspace and first project

To scaffold a new workspace called `dagster-workspace`, run `uvx create-dagster@latest workspace` and respond yes to the prompt to run `uv sync` after scaffolding:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/1-dg-scaffold-workspace.txt" />

The scaffolded workspace includes a `projects` folder, which is currently empty, and a `deployments` folder, which includes a `local` folder with a `pyproject.toml` file that specifies an environment for running `dg` commands locally against your workspace.

Next, enter the directory and activate the virtual environment for the `local` environment:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/2-activate-workspace-venv.txt" />

:::note

You'll need to activate this virtual environment anytime you open a new terminal session and want to run a `dg` command against the workspace.

:::

Now we'll create a project inside our workspace called `project-1`. Run `uvx create-dagster@latest project` with the path of the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/3-dg-scaffold-project.txt" />

This will create a new Python environment for this project and associate that project with the workspace.

### Workspace structure

The new workspace has the following structure:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/4-tree.txt" />

The `dg.toml` file for the `dagster-workspace` folder contains a `directory_type = "workspace"` setting that marks this directory as a workspace:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/workspace/5-dg.toml"
  language="TOML"
  title="dagster-workspace/dg.toml"
/>

:::note

`project-1` also contains a virtual environment directory called `.venv` that is not shown above. This environment is managed by `uv` and its contents are specified in the `uv.lock` file.

:::

The `project-1` directory contains a `pyproject.toml` file with a
`tool.dg.directory_type = "project"` section that defines it as a `dg` project:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/workspace/6-project-pyproject.toml"
  language="TOML"
  title="dagster-workspace/projects/project-1/pyproject.toml"
/>

## Adding a second project to the workspace

As noted above, environments are scoped per project. `dg` commands will only use the environment of `project-1` when you are inside the `project-1` directory.

Let's create another project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/7-scaffold-project.txt" />

Now there are two projects. You can list them with:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/workspace/8-project-list.txt" />

The workspace now has the following structure:

## Loading the projects in the workspace

Finally, let's load our two projects with `dg dev`. When you run `dg dev` from the workspace root, it will automatically recognize the projects in your workspace and launch each project in a separate process in its virtual environment found in the `.venv` folder in the project.

<CliInvocationExample contents="dg dev" />

{/* TODO - replace screenshot */}
![](/images/guides/build/projects-and-components/setting-up-a-workspace/two-projects.png)
