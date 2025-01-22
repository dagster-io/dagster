---
title: Custom Resource
description: Creating a custom resource
last_update:
  author: Dennis Hume
sidebar_position: 30
---

With the output we can now easily parse, we can use the NREL API to lookup nearby alternative fuel stations. The NREL API is a standard REST API and we can create a resource with a single method to retrieve fuel stations. This method (`alt_fuel_stations`) will take in the three parameters from our prompt engineering asset (latitue, longitude and fuel type). Here you can see another benefit of prompt engineering. The NREL API can limit our search to certain vechicle types but uses specific codes to denote these types. Our prompt accounts for these types and ensures that the parameters are met.

<CodeExample path="project_prompt_eng/project_prompt_eng/resources.py" language="python" lineStart="4" lineEnd="31"/>

Now we can use our custom resource in another asset (`nearest_fuel_station`) where will map the values from our AI asset to the resource method. The [reponse of the API](https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/nearest/#fuel-station-record-fields) gives some very rich data about these fuel stations. One field that would be particuarly interesting for the user would be `access_days_time` which shows when the fuel station is open. As we parse through the results in the assets we will limit the results to the first three fuel stations that have that information.

<CodeExample path="project_prompt_eng/project_prompt_eng/assets.py" language="python" lineStart="95" lineEnd="115"/>

We now have information about fuel stations.