---
title: 'Projects and workspaces'
description: 'Understanding the differences and relationship between the projects, workspaces and code locations'
sidebar_position: 500
---

Dagster uses several related terms to describe how your code is organized and deployed. While they may sound similar, each has a distinct meaning and purpose in the lifecycle of a Dagster deployment.

## Project

A **Dagster project** follows the general convention for a [Python project packaged for distribution](https://packaging.python.org/en/latest/tutorials/packaging-projects/): a structured collection of source files, libraries, and configuration used for a specific application. Additionally, Dagster projects contain [Dagster definitions](https://docs.dagster.io/api/dagster/definitions).

The recommended Dagster project layout looks like this:

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

While Dagster is flexible about how you organize your code, it provides an opinionated starting point with the [`create-dagster` CLI](/api/clis/create-dagster). For more information on creating Dagster projects from the CLI, see [Creating a new Dagster project](/guides/build/projects/creating-a-new-project).

## Code location

A [code location](/deployment/code-locations) is a Dagster project that can be loaded and accessed by Dagster tools, such as the UI, CLI, and Dagster+. A code location must contain a module with an instance of [`Definitions`](/api/dagster/definitions#dagster.Definitions) in a top-level variable and a Python environment that can load that module. Dagster projects created with the [`create-dagster` CLI](/api/clis/create-dagster) are also code locations. Whenever an asset runs in Dagster, it executes within the context of its code location, both the specific environment and project from which it originates.

![Code locations](/images/guides/deploy/code-locations/code-locations.png)

## Workspace

A workspace allows you to manage and orchestrate multiple Dagster projects together. This is useful when:

- Different teams maintain separate Dagster projects.
- Projects have distinct dependencies or environments.
- You want to deploy multiple projects in a coordinated way.


As with projects, Dagster provides an opinionated starting point for workspaces with the [`create-dagster` CLI](/api/clis/create-dagster). For more information on creating Dagster workspaces from the CLI, see [Managing multiple projects with workspaces](/guides/build/projects/multiple-projects).
