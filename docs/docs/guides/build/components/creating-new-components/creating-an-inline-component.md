---
description: Use the dg CLI to create and register an inline component.
sidebar_position: 200
title: Creating an inline component
---

Sometimes you need to define an _ad hoc_ component that you are unlikely to
reuse. In this situation, you can create an **inline component**. An inline
component is a component that is defined in the `defs` directory alongside
its instance definitions, rather than in a directory exposed to the dg registry
(e.g. the `components` directory in a standard `dg` project).

Let's say we want to define a set of assets with each asset being materialized
on its own schedule. This isn't a pattern we imagine
using elsewhere in our project, so we define these asset/schedule pairs using
an inline component.

To create the component, we use the `dg scaffold inline-component` command:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/generated/creating-an-inline-component/generated/1-dg-scaffold-defs-inline-component.txt" />

Supposing we are in a project called `my_project`, this will create a new
directory at `my_project/defs/assets_with_schedules` with two files.

`my_project/defs/assets_with_schedules/asset_with_schedule.py` contains a barebones
definition of the `AssetWithSchedule` component class:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/creating-an-inline-component/generated/2-asset-with-schedule-init.py"
  language="python"
  title="src/my_project/defs/assets_with_schedules/asset_with_schedule.py"
/>

Let's parameterize our component to take an asset key and a cron schedule
string, and output a corresponding `AssetsDefinition` and `ScheduleDefinition`.
Because this is just for illustrative purposes, we'll just generate random
numbers for the asset materialization function:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/creating-an-inline-component/asset-with-schedule-final.py"
  language="python"
  title="src/my_project/defs/assets_with_schedules/asset_with_schedule.py"
/>


`my_project/defs/assets_with_schedules/defs.yaml` starts us off with an instance of the new
component with no defined attributes:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/creating-an-inline-component/generated/3-assets-with-schedules-defs-init.py"
  language="yaml"
  title="src/my_project/defs/assets_with_schedules/defs.yaml"
/>


Note that there is nothing special about the `type` field. It is just a
fully-qualified Python object reference, as it is when defining instances of
registered components. The only difference between `AssetWithSchedule` and a
registered component is that `AssetWithSchedule` won't show up in the `dg`
registry.

We'll modify this file to define three instances of our component, each
representing an asset with a corresponding schedule:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/creating-an-inline-component/assets-with-schedules-defs-final.py"
  language="yaml"
  title="src/my_project/defs/assets_with_schedules/defs.yaml"
/>

If we now run `dg list defs`, we can see our three assets and schedules:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/generated/creating-an-inline-component/generated/4-dg-list-defs.txt" />

Now if we open this up in `dg dev` and look at the "Automations" tab, we should see three schedules targeting their corresponding assets:

![UI Deployment - Configuration tab](/images/guides/build/projects-and-components/components/inline-component-schedules.png)
