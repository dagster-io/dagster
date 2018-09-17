.. image:: https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png
   :align: center

.. docs-include

============
Introduction
============

Dagster is an opinionated system and programming model for data pipelines. This process goes by
many names -- ETL (extract-load-transform), ELT (extract-transform-load), model production, data
integration, and so on -- but in essence they all describe the same activity: Performing a set of
computations structured as a DAG (directed, acyclic graph) that end up producing data assets,
whether those assets be tables, files, machine-learning models, etc.

There are a few tools in this repo

This repo has a few primary components:

- **Dagster**: The core programming model and abstraction stack; a stateless single-node and -process execution engine; and a CLI tool for driving that engine.
* **Dagit**: Dagit is a rich viewer for Dagster assets.
* **Dagster GE**: A Dagster integration with Great Expectations. (see https://github.com/great-expectations/great_expectations)

Go to https://dagster.readthedocs.io/en/latest/ for documentation!