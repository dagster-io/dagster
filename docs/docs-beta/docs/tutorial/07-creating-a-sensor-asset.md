---
title: Event Driven Assets
description: Use sensors to create event driven pipelines
last_update:
  author: Alex Noonan
---

# Sensors 

There are several ways to automate pipelines and assets [in Dagster](guides/automation). 

In this step you will:

- Create an asset the runs based on a event driven workflow
- Create a sensor to listen for conditions to materialize the asset. 

## 1. Event Driven Asset


<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="274" lineEnd="311"/>


## 2. Build the Sensor

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="313" lineEnd="355"/>


## 3. Materialize the sensor asset

Your definitions object should now look like this:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="356" lineEnd="371"/>

## Next Steps

Now that we have our complete project, the next step is to refactor the project into more a more manageble structure so we can add to it as needed. 

Finish the tutorial with [refactoring the project](tutorial/refactoring-the-project)