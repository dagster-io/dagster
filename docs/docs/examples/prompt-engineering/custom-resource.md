---
title: Custom Resource
description: Creating a custom resource
last_update:
  author: Dennis Hume
sidebar_position: 40
---

With an output in our desired schema, we can use the [NREL](https://www.nrel.gov/) API to lookup nearby alternative fuel stations. The NREL API is a standard REST API. In Dagster, we will create a resource with a single method to retrieve fuel stations. This method (`alt_fuel_stations`) will take in the three parameters from our prompt engineering asset (latitude, longitude, and fuel type).

<CodeExample
  path="docs_projects/project_prompt_eng/project_prompt_eng/resources.py"
  language="python"
  startAfter="start_resource"
  endBefore="end_resource"
/>

Now we can use our custom resource in another asset (`nearest_fuel_station`) and query the API. The [response of the API](https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/nearest/#fuel-station-record-fields) gives some very rich data about these fuel stations. One field that would be particularly interesting for the user is `access_days_time` which shows when the fuel station is open.

<CodeExample
  path="docs_projects/project_prompt_eng/project_prompt_eng/assets.py"
  language="python"
  startAfter="start_nearest_fuel_stations"
  endBefore="end_nearest_fuel_stations"
/>

There is one problem with the `access_days_time` value: it is a free form string and contains values like `7am-7pm M-Th and Sat, 7am-8pm F, 9am-5pm Sun` and `24 hour service`. We can write a function to parse this out, but that would get messy quickly. Instead, we can pass it through our AI model again and use a different prompt.

## Next steps

- Continue this example with [additional prompt](/examples/prompt-engineering/additional-prompt)
