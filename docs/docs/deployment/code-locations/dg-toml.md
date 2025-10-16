---
description: Use a dg.toml file to configure open source Dagster code locations.
sidebar_position: 250
title: dg.toml reference (Dagster OSS)
---

import DagsterOSS from '@site/docs/partials/\_DagsterOSS.md';

<DagsterOSS />

A dg.toml file can be used to configure code locations in Dagster. It tells Dagster where to find your code and how to load it. This is a TOML format configuration file. For example:

```toml
# dg.toml
directory_type = "workspace"

[workspace]

[[workspace.projects]]
path = "my-project"
```

Each entry in a dg file is considered a code location. A code location should contain a single <PyObject section="definitions" module="dagster" object="Definitions" /> object. This is created automatically when projects are scaffolded with [`create-dagster` CLI](/guides/build/projects/creating-a-new-project).

## Location of the dg.toml

Dagster command-line tools (like `dg`) look for the dg file in the current directory when invoked. This allows you to launch from that directory without the need for command line arguments:

```bash
dg dev
```

## Multiple code locations

You can define multiple code locations in a single `dg.toml` file:

```toml
# dg.toml
directory_type = "workspace"

[workspace]

[[workspace.projects]]
path = "my-project-1"

[[workspace.projects]]
path = "my-project-2"
```

This assumes that both projects are nested within the current directory where the `dg.toml` file is located.

```
.
├── my-project-1
├── my-project-2
├── dg.toml
├── pyproject.toml
└── uv.lock
```

To load the `dg.toml` file from a different folder, use the `-w` argument:

```shell
dg dev -w path/to/dg.toml
```
