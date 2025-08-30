---
title: Using sensors in projects
sidebar_position: 250
description: Using sensors in Dagster dg projects for entities such as assets and jobs.
---

:::note Prerequisites

Before following this guide, you will need to [create a project](/guides/build/projects/creating-a-new-project) with the [`create-dagster` CLI](/api/clis/create-dagster).

:::

[Assets](/guides/build/assets) and [jobs](/guides/build/jobs) frequently use sensors that are instantiated elsewhere in the project.

For example, if you have created a new Dagster project with `dg` called `my_project`, you can define the sensors at `src/my_project/defs/sensors.py`:

Sensor binding can happen at any level of the `defs` hierarchy. If you moved `asset_one` in this example to a subdirectory, you could leave the existing `sensors.py` file at `src/defs/sensors.py`:

```
src
└── my_project
    └── defs
        ├── assets
        │   └── asset_one.py # contains def asset_one():
        └── sensors.py # contains dg.sensor
```

## Scaffolding sensors

To create a sensor dictionary like the above, you can run the following:

```bash
dg scaffold defs dagster.sensor sensors.py
```

which will create

<CodeExample
  path="docs_snippets/docs_snippets/concepts/automate/scaffolded-sensor-defs.py"
  title="src/<project_name>/defs/sensors.py"
/>

and you can fill out the sensor dictionary as needed.
