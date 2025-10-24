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

## Code location

A [code location](/guides/build/projects) is a Dagster project that can be loaded and accessed by Dagster tools, such as the UI, CLI, and Dagster+. A code location must contain a module with an instance of [`Definitions`](/api/dagster/definitions#dagster.Definitions) in a top-level variable and a Python environment that can load that module. Dagster projects created with the [`create-dagster` CLI](/api/clis/create-dagster) are also code locations. Whenever an asset runs in Dagster, it executes within the context of its code location, both the specific environment and project from which it originates.

![Code locations](/images/guides/deploy/code-locations/code-locations.png)

------- TK clean up below

A code location is a collection of Dagster definitions loadable and accessible by Dagster's tools, such as the CLI, UI, and Dagster+. A code location comprises:

- A reference to a Python module that has an instance of <PyObject section="definitions" module="dagster" object="Definitions" /> in a top-level variable
- A Python environment that can successfully load that module

Definitions within a code location have a common namespace and must have unique names. This allows them to be grouped and organized by code location in tools.

![Code locations](/images/guides/deploy/code-locations/code-locations-diagram.png)

A single deployment can have one or multiple code locations.

Code locations are loaded in a different process and communicate with Dagster system processes over an RPC mechanism. This architecture provides several advantages:

- When there is an update to user code, the Dagster webserver/UI can pick up the change without a restart.
- You can use multiple code locations to organize jobs, but still work on all of your code locations using a single instance of the webserver/UI.
- The Dagster webserver process can run in a separate Python environment from user code so job dependencies don't need to be installed into the webserver environment.
- Each code location can be sourced from a separate Python environment, so teams can manage their dependencies (or even their Python versions) separately.

## Workspace

A workspace allows you to manage and orchestrate multiple Dagster projects together. This is useful when:

- Different teams maintain separate Dagster projects.
- Projects have distinct dependencies or environments.
- You want to deploy multiple projects in a coordinated way.


As with projects, Dagster provides an opinionated starting point for workspaces with the [`create-dagster` CLI](/api/clis/create-dagster). For more information on creating Dagster workspaces from the CLI, see [Managing multiple projects with workspaces](/guides/build/projects/managing-multiple-projects).