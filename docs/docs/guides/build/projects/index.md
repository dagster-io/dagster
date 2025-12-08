---
description: Learn how to build Dagster projects, turn them into code locations that can be deployed to the cloud, and manage multiple projects with workspaces. 
sidebar_position: 10
title: Projects and workspaces
canonicalUrl: "/guides/build/projects"
slug: "/guides/build/projects"
---

Dagster uses several related terms to describe how your code is organized and deployed. While they may sound similar, each has a distinct meaning and purpose in the lifecycle of a Dagster deployment.

## Projects

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

### Creating projects

While Dagster is flexible about how you organize your code, we provide an opinionated starting point with the [`create-dagster` CLI](/api/clis/create-dagster). See [Creating Dagster projects](/guides/build/projects/creating-projects) to learn how to create Dagster projects from the CLI.

### Deploying projects

To make your Dagster project deployable to Dagster+, you will need to create additional configuration files. For more information, see the [Dagster+ CI/CD guide](/deployment/dagster-plus/deploying-code/configuring-ci-cd).

## Workspaces

Workspaces allow you to manage and orchestrate multiple Dagster projects together. This is useful when:

- Different teams maintain separate Dagster projects.
- Projects have distinct dependencies or environments.
- You want to deploy multiple projects in a coordinated way.

### Creating workspaces

As with projects, Dagster provides an opinionated starting point for workspaces with the [`create-dagster` CLI](/api/clis/create-dagster). See [Creating workspaces to manage multiple projects](/guides/build/projects/workspaces/creating-workspaces) to learn how to create Dagster workspaces from the CLI.
