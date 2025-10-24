---
title: Using schedules in Dagster projects
sidebar_position: 250
description: Using schedules in Dagster dg projects for entities such as assets and jobs.
---

:::note Prerequisites

Before following this guide, you will need to [create a project](/guides/build/projects/creating-dagster-projects) with the [`create-dagster` CLI](/api/clis/create-dagster).

:::

[Assets](/guides/build/assets) and [jobs](/guides/build/jobs) frequently use schedules that are instantiated elsewhere in the project.

For example, if you have created a new Dagster project with `dg` called `my_project`, you can define the schedules at `src/my_project/defs/schedules.py`:

Schedule binding can happen at any level of the `defs` hierarchy. If you moved `asset_one` in this example to a subdirectory, you could leave the existing `schedules.py` file at `src/defs/schedules.py`:

```
src
└── my_project
    └── defs
        ├── assets
        │   └── asset_one.py # contains def asset_one():
        └── schedules.py # contains dg.schedule
```

## Scaffolding schedules

To create a schedule dictionary like the above, you can run the following:

```bash
dg scaffold defs dagster.schedule path/to/schedules.py
```

which will create

<CodeExample
  path="docs_snippets/docs_snippets/concepts/automate/scaffolded-schedule-defs.py"
  title="src/<project_name>/defs/schedules.py"
/>

and you can fill out the schedule dictionary as needed.
