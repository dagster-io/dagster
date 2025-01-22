---
title: Custom Resource
description: Creating a custom resource
last_update:
  author: Dennis Hume
sidebar_position: 30
---

With an output we can easily parse, we can use the NREL API to lookup nearby alternative fuel stations. The NREL API is a standard REST API and we can create a resource with a single method to retrieve fuel stations. This method (`alt_fuel_stations`) will take in the three parameters from our prompt engineering asset (latitude, longitude and fuel type). Here you can see another benefit of prompt engineering. The NREL API can limit our search to certain vehicle types but uses specific codes to denote these types. Our prompt accounts for these types and ensures that the parameters are met.

<CodeExample path="project_prompt_eng/project_prompt_eng/resources.py" language="python" lineStart="4" lineEnd="31"/>

Now we can use our custom resource in another asset (`nearest_fuel_station`) where will map the values from our AI asset to the resource method. The [reponse of the API](https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/nearest/#fuel-station-record-fields) gives some very rich data about these fuel stations. One field that would be particularly interesting for the user would be `access_days_time` which shows when the fuel station is open. As we parse through the results in the assets we will limit the results to the first three fuel stations that have that information.

<CodeExample path="project_prompt_eng/project_prompt_eng/assets.py" language="python" lineStart="95" lineEnd="115"/>

Using the `access_days_time` we can tell the user if their nearby fuel stations are open. However if we look at the value for `access_days_time` it is not a particularly helpful string: `7am-7pm M-Th and Sat, 7am-8pm F, 9am-5pm Sun`. We can write a function to parse this out, but that would get messy quickly. Instead we can pass it through our AI model again and use a different prompt.

## Next steps

- Continue this tutorial with [additional prompt](additional-prompt)