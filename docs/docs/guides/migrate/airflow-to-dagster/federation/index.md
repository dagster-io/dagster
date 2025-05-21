---
description: Use dagster-airlift to observe DAGs from multiple Airflow instances and federate execution between them using Dagster as a centralized control plane, all without changing your Airflow code.
sidebar_position: 10
title: Federate execution across Airflow instances with Dagster
---

You can use `dagster-airlift` to observe DAGs from multiple Airflow instances and federate execution between them using Dagster as a centralized control plane, all without changing your Airflow code.

## Tutorial overview

In this tutorial, a data platform team is tasked with managing the following Airflow setup:

- An Airflow instance called `warehouse`, run by another team, that contains a DAG called `warehouse.load_customers` that loads customer data into the data warehouse.
- An Airflow instance called `metrics`, run by the data platform team, that contains a DAG called `metrics.customer_metrics` that computes metrics on top of the customer data.

The data platform team wants to update this setup to only rebuild the `metrics.customer_metrics` DAG when the `warehouse.load_customers` DAG has new data. They can't observe or control this cross-instance dependency in the current setup, so they decide to use `dagster-airlift`.

We'll walk you through an example of using `dagster-airlift` to observe the `warehouse` and `metrics` Airflow instances described above, and set up a federated execution controlled by Dagster that only triggers the `metrics.customer_metrics` DAG when the `warehouse.load_customers` DAG has new data, all without requiring any changes to Airflow code.

## Next steps

To get started with this tutorial, follow the [setup steps](/guides/migrate/airflow-to-dagster/federation/setup) to install the example code, set up a local environment, and run two instances of Airflow locally.
