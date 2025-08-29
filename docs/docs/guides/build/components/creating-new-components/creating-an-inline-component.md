---
description: Use the dg CLI to create and register an inline component.
sidebar_position: 100
title: Creating an inline component
---

Sometimes you need to define an _ad hoc_ component that you are unlikely to
reuse. In this situation, you can create an **inline component**. An inline
component is a component that is defined in the `defs` directory alongside
its instance definitions, rather than in a directory exposed to the dg registry
(e.g. the `components` directory in a standard `dg` project).

Let's say we want to define a set of assets with each asset being materialized
on its own independently variable schedule. This isn't a pattern we imagine
using elsewhere in our project, so we define these asset/schedule pairs using
an inline component.

To create the component, we use the `dg scaffold inline-component` command:

```
dg scaffold defs inline-component --typename AssetWithSchedule
assets_with_schedules
```

Supposing we are in a project called `my_project`, this will create a new
directory at `my_project/defs/assets_with_schedules` with two files.

`my_project/defs/assets_with_schedules/asset_with_schedule.py` contains a barebones
definition of the `AssetWithSchedule` component class:

```
import dagster as dg

class AssetWithSchedule(dg.Component, dg.Model, dg.Resolvable):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
```

Let's parameterize our component to take an asset key and a cron schedule
string, and output a corresponding `AssetsDefinition` and `ScheduleDefinition`.
Because this is just for illustrative purposes, we'll just generate random
numbers for the asset materialization function:

```
from random import randint
import dagster as dg

class AssetWithSchedule(dg.Component, dg.Model, dg.Resolvable):

    asset_key: list[str]
    cron_schedule: str

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:

        @dg.asset(key=dg.AssetKey(self.asset_key))
        def asset():
            return randint(1, 100)

        schedule = dg.ScheduleDefinition(
            name=f"{'_'.join(self.asset_key)}_schedule",
            cron_schedule=self.cron_schedule,
            target=asset,
        )

        return dg.Definitions(assets=[asset], schedules=[schedule])
```

`defs/assets_with_schedules/defs.yaml` starts us off with an instance of the new
component with no defined attributes:

```yaml
type: my_project.defs.assets_with_schedules.asset_with_schedule.AssetWithSchedule
attributes: {}
```

Note that there is nothing special about the `type` field-- it is just a
fully-qualified Python object reference, as it is when defining instances of
registered components. The only difference between `AssetWithSchedule` and a
registered component is that `AssetWithSchedule` won't show up in the `dg`
registry.

We'll modify this file to define three instances of our component, each
representing an asset with a corresponding schedule:

```yaml
type: my_project.defs.assets_with_schedules.asset_with_schedule.AssetWithSchedule
attributes:
  asset_key: ["foo"]
  cron_schedule: "*/10 * * * *"
---
type: my_project.defs.assets_with_schedules.asset_with_schedule.AssetWithSchedule
attributes:
    asset_key: ["bar"]
    cron_schedule: "*/20 * * * *"
---
type: my_project.defs.assets_with_schedules.asset_with_schedule.AssetWithSchedule
attributes:
  asset_key: ["baz"]
  cron_schedule: "*/30 * * * *"
```

Now if we open this up in `dg dev` and look at the "Automations" tab, we should see three schedules targeting their corresponding assets:

![UI Deployment - Configuration tab](/images/guides/build/projects-and-components/components/inline-component-schedules.png)
