---
title: 'Lesson 6: Overview'
module: 'dagster_essentials'
lesson: '6'
---

# Overview

In previous lessons, you learned about assets, how to connect assets to represent a data pipeline, and how to start a run that materializes the assets.

Dagster’s role is to be the single pane of glass across all data pipelines in an organization. To make this possible, Dagster needs to know about the services and systems used in your data pipelines, such as cloud storage or a data warehouse. In this lesson, we’ll show you how to accomplish this using software engineering best practices.

With this in mind, the best practice we’ll focus on in this lesson is called **Don’t Repeat Yourself**, or **DRY** for short. This principle recommends that engineers do something once and only once, thereby reducing duplication and redundancy. By being intentional and writing DRY code, you can reduce the number of bugs, increase the ability to understand the project’s codebase, and improve observability over how logic and functionality are used.

Another way Dagster embraces software engineering best practices is by enabling testing in development. Developing and changing pipelines get more daunting as complexity increases. Testing in development and having a place to test changes is critical to building confidence in the code before it gets to production. This has been a challenge in data engineering with the code and environments tightly coupled.

In Dagster, connections to databases can be swapped with local databases and external connections can be represented differently for each environment. A replica of a production environment can be modeled and used in development to take the guessing out of building and making changes to your pipelines.
