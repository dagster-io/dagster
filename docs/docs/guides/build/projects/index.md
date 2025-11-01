---
description: Learn how to build Dagster projects, turn them into code locations that can be deployed to the cloud, and manage multiple projects with workspaces. 
sidebar_position: 10
title: Projects and workspaces
canonicalUrl: "/guides/build/projects"
slug: "/guides/build/projects"
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

While Dagster is flexible about how you organize your code, it provides an opinionated starting point with the [`create-dagster` CLI](/api/clis/create-dagster). For more information on creating Dagster projects from the CLI, see [Creating Dagster projects](/guides/build/projects/creating-dagster-projects).

To make your Dagster project deployable to Dagster+, you will need to create additional configuration files. For more information, see [Deploying Dagster projects](/guides/build/projects/deploying-dagster-projects).

A single deployment of Dagster can contain multiple projects organized into workspaces.

## Workspace

A workspace allows you to manage and orchestrate multiple Dagster projects together. This is useful when:

- Different teams maintain separate Dagster projects.
- Projects have distinct dependencies or environments.
- You want to deploy multiple projects in a coordinated way.


As with projects, Dagster provides an opinionated starting point for workspaces with the [`create-dagster` CLI](/api/clis/create-dagster). To learn how to create a Dagster workspaces from the CLI, see [Creating workspaces to manage multiple projects](/guides/build/projects/workspaces/managing-multiple-projects).
