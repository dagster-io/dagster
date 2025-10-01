---
title: Using jobs in Dagster projects
sidebar_position: 600
description: Using jobs in Dagster dg projects for entities such as assets .
---

:::note Prerequisites

Before following this guide, you will need to [create a project](/guides/build/projects/creating-a-new-project) with the [`create-dagster` CLI](/api/clis/create-dagster).

:::

[Assets](/guides/build/assets) frequently use jobs that are instantiated elsewhere in the project.

For example, if you have created a new Dagster project with `dg` called `my_project`, you can define the jobs at `src/my_project/defs/jobs.py`:

Job binding can happen at any level of the `defs` hierarchy. If you moved `asset_one` in this example to a subdirectory, you could leave the existing `jobs.py` file at `src/defs/jobs.py`:

```
src
└── my_project
    └── defs
        ├── assets
        │   └── asset_one.py # contains def asset_one():
        └── jobs.py # contains dg.job
```

## Scaffolding jobs

To create a job dictionary like the above, you can run the following:

```bash
dg scaffold defs dagster.job path/to/jobs.py
```

which will create

<CodeExample path="docs_snippets/docs_snippets/concepts/automate/scaffolded-job-defs.py"  title="src/<project_name>/defs/jobs.py" />

and you can fill out the job dictionary as needed.