---
title: 'Comparing projects vs workspaces vs code locations'
description: 'Understanding the differences and relationship between the projects, workspaces and code locations'
sidebar_position: 50
---

Dagster uses several related terms to describe how your code is organized and deployed. While they may sound similar, each has a distinct meaning and purpose in the lifecycle of a Dagster deployment.

## Project

A **Dagster project** follows the general convention for a [Python project packaged for distribution](https://packaging.python.org/en/latest/tutorials/packaging-projects/): a structured collection of source files, libraries, and configuration used for a specific application. Additionally, Dagster projects contain [Dagster definitions](https://docs.dagster.io/api/dagster/definitions).

The recommended Dagster project layout looks like this:

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

While Dagster is flexible about how you organize your code, it provides an opinionated starting point with the [`create-dagster` CLI](/api/clis/create-dagster). For more information on creating Dagster projects from the CLI, see [Creating a new Dagster project](/guides/build/projects/creating-a-new-project).


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





## Workspace

A workspace allows you to manage and orchestrate multiple Dagster projects together. This is useful when:

- Different teams maintain separate Dagster projects.
- Projects have distinct dependencies or environments.
- You want to deploy multiple projects in a coordinated way.


As with projects, Dagster provides an opinionated starting point for workspaces with the [`create-dagster` CLI](/api/clis/create-dagster). For more information on creating Dagster workspaces from the CLI, see [Managing multiple projects with workspaces](/guides/build/projects/multiple-projects).

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
path = "projects/my-project-1"

[[workspace.projects]]
path = "projects/my-project-2"
```

Running commands like `dg check defs` from the base environment will automatically apply to each configured project. And `dg dev` will launch Dagster with both projects.

## Code location

A code location represents a loadable Dagster [`Definitions`](/api/dagster/definitions#dagster.Definitions) object, a combination of the Python module and the Python environment where it runs. Code locations are the fundamental units of organization within a Dagster deployment. They define what Dagster loads, executes, and observes.

In other words, code locations are how your Dagster deployment interacts with your projects. A single deployment can include multiple code locations, each corresponding to a different project or environment.

![Code locations](/images/guides/deploy/code-locations/code-locations.png)

