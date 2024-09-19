---
title: 'Lesson 9: Overview'
module: 'dagster_essentials'
lesson: '9'
---

# Overview

In Lesson 7, you wrote a schedule to run your pipelines every month. Using schedules is only one of the various ways to trigger asset materializations in Dagster.

Event-driven runs are common in real life. When running our bakery, we may get deliveries of ingredients and need to move them into the kitchen. Just like in baking cookies, data pipelines may also need to be responsive and reactive to events. In Dagster, you can use **sensors** to automate your pipelines for these situations.
