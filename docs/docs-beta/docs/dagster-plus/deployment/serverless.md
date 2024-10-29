---
title: 'Serverless deployment'
displayed_sidebar: 'dagsterPlus'
sidebar_position: 1
---

# Serverless deployment

Dagster+ Serverless is a fully managed version of Dagster+ and is the easiest way to get started with Dagster. With a Serverless deployment, you can run your Dagster jobs without spinning up any infrastructure yourself.

---

## When to choose Serverless \{#when-to-choose-serverless}

Serverless works best with workloads that primarily orchestrate other services or perform light computation. Most workloads fit into this category, especially those that orchestrate third-party SaaS products like cloud data warehouses and ETL tools.

If any of the following are applicable, you should select [Hybrid deployment](/dagster-plus/deployment/hybrid):

- You require substantial computational resources. For example, training a large machine learning (ML) model in-process
- Your dataset is too large to fit in memory. For example, training a large ML model in-process on a terabyte of data
- You need to distribute computation across many nodes for a single run. Dagster+ runs currently execute on a single node with 4 CPUs
- You don't want to add Dagster Labs as a data processor

---

## Limitations \{#limitations}

Serverless is subject to the following limitations:

- Maximum of 100 GB of bandwidth per day
- Maximum of 4500 step-minutes per day
- Runs receive 4 vCPU cores, 16 GB of RAM, and 128 GB of ephemeral disk
- Code locations receive 0.25 vCPU cores and 1 GB of RAM
- All Serverless jobs run in the United States
- Infrastructure cannot be customized or extended, such as using additional containers

Dagster+ Pro customers may request a quota increase by [contacting Sales](https://dagster.io/contact).

---

## Next steps

To start using Dagster+ Serverless, follow our [Getting started with Dagster+](/dagster-plus/getting-started) guide.
