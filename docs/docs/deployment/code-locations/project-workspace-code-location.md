---
title: 'Comparing projects vs workspaces vs code locations'
description: 'Understanding the differences and relationship between the projects, workspaces and code locations'
sidebar_position: 50
---

Dagster uses several related terms to describe how your code is organized and deployed. While they may sound similar, each has a distinct meaning and purpose in the lifecycle of a Dagster deployment.

## Project

A **project** follows the general Python convention, a structured collection of source files, libraries, and configuration used for a specific application. The recommended Python project layout (centered around a `pyproject.toml`) looks like this:

```
my-project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       └── module.py
├── tests/
│   └── test_module.py
├── docs/
├── pyproject.toml
├── README.md
└── LICENSE.txt
```

Dagster adopts this same concept. A Dagster project is simply a Python project containing Dagster definitions. While Dagster is flexible about how you organize your code, it provides an opinionated starting point via the [`create-dagster` CLI](/api/clis/create-dagster).

```bash
uvx create-dagster@latest project my-project
```

```
my-project/
├── pyproject.toml
├── README.md
├── src
│   └── my_project
│       ├── __init__.py
│       ├── definitions.py
│       └── defs
│           └── __init__.py
├── tests
│   └── __init__.py
└── uv.lock
```

The generated `pyproject.toml` defines the root module and registry modules for the project:

```toml
# pyproject.toml
...

[tool.dg]
directory_type = "project"

[tool.dg.project]
root_module = "my_project"
registry_modules = [
    "my_project.components.*",
]
```

## Workspace

A workspace allows you to manage and orchestrate multiple Dagster projects together. This is useful when:

- Different teams maintain separate Dagster projects.
- Projects have distinct dependencies or environments.
- You want to deploy multiple projects in a coordinated way.

A workspace acts as an orchestration layer above individual projects, enabling multi-project deployments while maintaining isolation between them.

To create a workspace that includes multiple projects:

```bash
mkdir projects
uvx create-dagster@latest project projects/my-project-1
uvx create-dagster@latest project projects/my-project-2
```

This results in a structure like:

```
.
├── projects
│   ├── my-project-1
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── src
│   │   │   └── my_project_1
│   │   │       ├── __init__.py
│   │   │       └── definitions.py
│   │   ├── tests
│   │   │   └── __init__.py
│   │   └── uv.lock
│   └── my-project-2
│       ├── pyproject.toml
│       ├── README.md
│       ├── src
│       │   └── my_project_2
│       │       ├── __init__.py
│       │       └── definitions.py
│       ├── tests
│       │   └── __init__.py
│       └── uv.lock
├── pyproject.toml
├── README.md
└── uv.lock
```

Each project remains self-contained and can be developed independently. The workspace configuration (`dg.toml`) then defines which projects belong to it:

```toml
# dg.toml
directory_type = "workspace"

[workspace]

[[workspace.projects]]
path = "projects/my-project-1

[[workspace.projects]]
path = "projects/my-project-2"
```

Running commands like `dg check defs` from the base environment will automatically apply to each configured project. And `dg dev` will launch Dagster with both projects.

## Code location

A code location represents a loadable Dagster [`Definitions`](/api/dagster/definitions#dagster.Definitions) object, a combination of the Python module and the Python environment where it runs. Code locations are the fundamental units of organization within a Dagster deployment. They define what Dagster loads, executes, and observes.

In other words, code locations are how your Dagster deployment interacts with your projects. A single deployment can include multiple code locations, each corresponding to a different project or environment.

![Code locations](/images/guides/deploy/code-locations/code-locations.png)

Whenever an asset runs in Dagster, it executes within the context of its code location, both the specific environment and project from which it originates.
