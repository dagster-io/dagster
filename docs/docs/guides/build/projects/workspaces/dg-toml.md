---
description: Use a dg.toml file to configure Dagster projects for production OSS deployments.
sidebar_position: 2000
title: dg.toml reference
---

A `dg.toml` file can be used to configure [workspaces](/guides/build/projects/workspaces/creating-workspaces) in Dagster OSS. It tells Dagster where to find your code and how to load it, in TOML format, and is created automatically when you create a workspace from the command line with `create-dagster workspace`. For example:

```toml
# dg.toml
directory_type = "workspace"

[workspace]

[[workspace.projects]]
path = "my-project"
```

:::tip

To create Dagster projects that can be loaded by Dagster, see [Creating Dagster projects](/guides/build/projects/creating-projects).

:::

## Location of the `dg.toml` file

Dagster command line tools (like [`dg`](/api/clis/dg-cli/dg-cli-reference)) look for the `dg.toml` file in the current directory when invoked. This allows you to launch the Dagster webserver/UI and load your projects from the current directory without command line arguments:

```bash
dg dev
```

To load the `dg.toml` file from a different folder, use the `-w` argument:

```shell
dg dev -w path/to/dg.toml
```
