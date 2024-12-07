---
title: Event Driven Assets
description: Use sensors to create event driven pipelines
last_update:
  author: Alex Noonan
---

# Sensors 

When building data pipelines, sometimes you need to use event driven automations to support situations where jobs occur at irregular cadences or in rapid succession. [Sensors](guides/sensors) is the building block in Dagster you can use to support this. 

In this step you will:

- Create an asset the runs based on a event driven workflow
- Create a sensor to listen for conditions to materialize the asset. 

## 1. Event Driven Asset

For our pipeline, we want to model a situation where an executive wants a pivot table report of sales results by department and product. They want that processed in real time from their request and it isnt a high priority to build the reporting to have this available and refreshing. 

For this asset we need to define the structure of the request that it is expecting in the materialization context. 

Other than that defining this asset is the same as our previous assets. Copy the following code beneath `product_performance` 

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="274" lineEnd="311"/>

## 2. Build the Sensor



<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="313" lineEnd="355"/>


## 3. Materialize the sensor asset

1. Update definitions object:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="356" lineEnd="371"/>

2. Reload definitions

3. Turn on sensor 

4. Add example JSON file to sensor folder

5. Navigate to asset page

-- need screenshot of asset materializing

## Next Steps

Now that we have our complete project, the next step is to refactor the project into more a more manageble structure so we can add to it as needed. 

Finish the tutorial with [refactoring the project](tutorial/refactoring-the-project)