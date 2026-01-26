---
description: "Dagster's resources system can be used with sensors to make it easier to call out to external systems and to make components of a sensor easier to plug in for testing purposes."
sidebar_position: 100
title: Using resources in sensors
---

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

Dagster's [resources](/guides/build/external-resources) system can be used with sensors to make it easier to call out to external systems and to make components of a sensor easier to plug in for testing purposes.

To specify resource dependencies, annotate the resource as a parameter to the sensor's function. Resources are provided by attaching them to your <PyObject section="definitions" module="dagster" object="Definitions" /> call.

Here, a resource is provided which provides access to an external API. The same resource could be used in the job or assets that the sensor triggers.

<CodeExample
  path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py"
  startAfter="start_new_resource_on_sensor"
  endBefore="end_new_resource_on_sensor"
  dedent="4"
  title="src/<project_name>/defs/assets.py"
/>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py"
  startAfter="start_new_resource_on_sensor_defs"
  endBefore="end_new_resource_on_sensor_defs"
  dedent="4"
  title="src/<project_name>/defs/resources.py"
/>

For more information on resources, refer to the [Resources documentation](/guides/build/external-resources). To see how to test schedules with resources, refer to the section on testing sensors with resources in [Testing sensors](/guides/automate/sensors/testing-sensors).
