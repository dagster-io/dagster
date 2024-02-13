---
title: "Lesson 9: What's a sensor?"
module: 'dagster_essentials'
lesson: '9'
---

# What's a sensor?

Sensors are a way to programmatically monitor a specific event and create runs based on it. Sensors continuously check and execute logic to know whether to kick off a run. By default, sensors in Dagster poll every 30 seconds. They are commonly used for situations where you want to materialize an asset after something else happens, such as:

- A new file arrives in a specific location, such as Amazon S3
- Another asset elsewhere has materialized
- An external system has freed up a worker slot

---

## In this lesson

In this lesson, we’ll assume a hypothetical scenario. Assume that the stakeholders for your taxi trip reports have been doing some ad hoc, exploratory analysis of how many trips happen in certain boroughs (ex. Manhattan or Brooklyn) throughout certain time ranges. They want to answer questions such as:

> "How do the December holidays impact ridership during rush hour in Manhattan?"

They’ve been asking you similar questions, and it’s been taking up lots of your time and bandwidth. Therefore, you’d like to automate this process to enable self-service reporting for your stakeholders.

You’ve created a request intake form that generates a structured JSON with the request and inserts them into the `data/requests` directory of your Dagster project. Now, you’ll automate answering these ad hoc requests by having a sensor listen to new requests come in. When a new JSON file representing a request lands in the directory, the sensor is triggered and materializes the asset. When the sensor has already materialized a report for all updated files in the directory, the sensor doesn’t kick off any materializations.

To fulfill the requirements above, we’ll:

1. Write a way to customize the asset materialization per request
2. Write a new asset that creates a report per request
3. Add a sensor to listen to requests come in
