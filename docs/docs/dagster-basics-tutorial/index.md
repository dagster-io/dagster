---
title: Dagster basics tutorial
description: Learn about Dagster basics, such as projects, assets, resources, asset dependencies, asset checks, automation, and components.
last_update:
  author: Dennis Hume
sidebar_class_name: hidden
canonicalUrl: '/dagster-basics-tutorial'
slug: '/dagster-basics-tutorial'
---

In this tutorial, you will learn about core Dagster features and use them to build a working data pipeline. We will start with the fundamental concepts and progress to higher level abstractions that showcase the power of Dagster.

By the end, you will be ready to build your own data pipelines and explore more advanced features and integrations.

## Dagster's programming model

Dagster’s programming model is built on three concepts that work together: `Components`, `Definitions`, and `Ops`. Each concept has a different level of abstraction and purpose, and together they let you move smoothly from high-level configuration to low-level execution.

- **`Components`** generate one or more `Definitions` based on configuration you provide. This allows you to avoid repetitive code by producing multiple `Definitions` automatically from a common pattern.

- **`Definitions`** are the building blocks of Dagster. `Definitions` combine metadata (what the entity, such an asset, represents) with a Python function called an `Op` (how the entity behaves). `Definitions` are what you actually execute in a Dagster job or run.

- **`Ops`**, short for "operations", are the lowest-level execution units. They are Python functions that represent the most basic unit of computation in Dagster.

![2048 resolution](/images/tutorial/dagster-tutorial/overviews/overview-1.png)

If you’d like to learn about the full set of Dagster features and how they interact with each other, check out our [Concepts page](/getting-started/concepts).

## Prerequisites

To follow the steps in this tutorial, you'll need:

- Python 3.9+ and a Python package manager. For more information, see the [Installation guide](/getting-started/installation).
- Familiarity with Python and SQL.
- A basic understanding of data pipelines.

You are now ready to starting building with Dagster.
