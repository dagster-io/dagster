---
title: Build a Dagster Pipeline
description: Learn how to build a pipeline with Dagster
last_update:
  author: Dennis Hume
sidebar_class_name: hidden
canonicalUrl: '/dagster-basics-tutorial'
slug: '/dagster-basics-tutorial'
---

# Build your first Dagster pipeline

In this tutorial, you’ll learn how to build a Dagster pipeline from the ground up. We will start with the fundamental concepts and progress to higher level abstractions that showcase the power the Dagster.

By the end, you’ll have a clear understanding of Dagster’s core features and how they work together to create data workflows.

## Dagster Layers

Dagster’s programming model is built on three layers that work together: `Components`, `Definitions`, and `Ops`. Each layer has a different level of abstraction and purpose, and together they let you move smoothly from high-level configuration to low-level execution.

- **Components: Build Definitions programmatically**
  `Components` sit one layer above `Definitions`. They are like factories that generate one or more `Definitions` based on configuration you provide. This allows you to avoid repetitive code by producing multiple `Definitions` automatically from a common pattern.

- **Definitions: Describe what something is and how it works**
  `Definitions` are the building blocks of Dagster. They combine metadata (what the entity represents) with a Python function (how it behaves). `Definitions` are what you actually execute in a Dagster job or run.

- **Ops: The low-level execution unit**
  At the lowest layer are `Ops` (short for “operations”). `Ops` are simple Python functions that represent the most basic unit of computation in Dagster.

<p align="center">
  <img src="/images/tutorial/dagster-tutorial/overviews/overview-1.png" alt="2048 resolution" width="25%" />
</p>

If you’d like to dive deeper into specific Dagster features and how they interact, check out our [Concepts page](/getting-started/concepts).

## Prerequisites

To follow the steps in this tutorial, you'll need:

- Python 3.9+ and a Python package manager. For more information, see the [Installation guide](/getting-started/installation).
- Familiarity with Python and SQL.
- A basic understanding of data pipelines.

You are now ready to starting building with Dagster.
