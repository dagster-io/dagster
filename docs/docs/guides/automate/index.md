---
title: 'Automate'
description: Learn how to automate your data pipelines.
sidebar_class_name: hidden
---

Automation is key to building reliable, efficient data pipelines. Dagster offers several ways to automate pipeline execution to fit a variety of needs.

Consider these factors when selecting an automation method:

- **Pipeline structure**: Are you working primarily with [assets](/guides/build/assets/), [ops](/guides/build/ops/), or a mix?
- **Timing requirements**: Do you need regular updates or event-driven processing?
- **Data characteristics**: Is your data partitioned? Do you need to update historical data?
- **System integration**: Do you need to react to external events or systems?

## Automation methods

| Method                                            | Description                                                                                                                  | Best for                                                     | Works with          |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------- |
| [Schedules](schedules/)                           | Run a [selection of assets](/guides/build/assets/asset-selection-syntax) at specified times with a cron expression           | Regular, time-based job runs and basic time-based automation | Assets, Ops, Graphs |
| [Declarative automation](declarative-automation/) | A framework that allows you to set automation conditions on assets and asset checks                                          | Asset-centric, condition-based updates                       | Assets only         |
| [Sensors](sensors/)                               | Trigger runs based on events or conditions that you define, like the arrival of a new file or a change to an external system | Event-driven automation                                      | Assets, Ops, Graphs |
| [Asset sensors](/guides/automate/asset-sensors)   | Trigger jobs when specified assets are materialized, allowing you to create dependencies between jobs or code locations.     | Cross-job/location asset dependencies                        | Assets only         |
| [GraphQL triggers](/guides/operate/graphql/)      | Trigger materializations and jobs from the GraphQL endpoint                                                                  | Event triggers from external systems                         | Assets, Ops, Jobs   |
