---
title: Migrating from workspace.yaml to dg.toml
sidebar_position: 2000
description: Migrate legacy workspace.yaml configurations to a dg.toml workspace.
unlisted: true
---

If you have an existing `workspace.yaml` file, you can migrate to a `dg.toml`-based workspace to align with the current Dagster OSS project and workspace structure.

## Overview

`workspace.yaml` directly lists code locations. A `dg.toml` workspace points to one or more Dagster projects, each with its own project configuration. The migration is therefore a move from "direct code locations" to "workspace + projects."

## Step 1: Create a workspace root

If you don't already have a workspace directory, create one by following [Creating workspaces](/guides/build/projects/workspaces/creating-workspaces). This will create a workspace root with a `dg.toml` file.

## Step 2: Convert code locations into projects

Each entry in `workspace.yaml` should map to a Dagster project in your workspace:

1. For each code location, create a Dagster project using [Creating projects](/guides/build/projects/creating-projects).
2. Move or reference your existing definitions in that project.
3. Add each project path under `[[workspace.projects]]` in `dg.toml`.

For the full `dg.toml` format, see the [dg.toml reference](/guides/build/projects/workspaces/dg-toml).

## Step 3: Validate and remove workspace.yaml

Run the workspace from the root directory:

```shell
dg dev
```

If everything loads correctly, you can remove `workspace.yaml` and update any scripts to point to `dg.toml` (for example, `dg dev -w path/to/dg.toml`).
