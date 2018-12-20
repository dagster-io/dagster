.. image:: https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png
   :align: center

.. docs-include

.. image:: https://coveralls.io/repos/github/dagster-io/dagster/badge.svg?branch=master
   :target: https://coveralls.io/github/dagster-io/dagster?branch=master
.. image:: https://circleci.com/gh/dagster-io/dagster.svg?style=svg
   :target: https://circleci.com/gh/dagster-io/dagster
.. image:: https://readthedocs.org/projects/dagster/badge/?version=latest
   :target: https://dagster.readthedocs.io/en/latest/

============
Introduction
============

Dagster is an opinionated system and programming model for data pipelines. This process goes by
many names -- ETL (extract-transform-load), ELT (extract-load-transform), model production, data
integration, and so on -- but in essence they all describe the same activity: performing a set of
computations structured as a DAG (directed, acyclic graph) that end up producing data assets,
whether those assets be tables, files, machine-learning models, etc.

This repository contains a number of distinct subprojects:

- **dagster**: The core programming model and abstraction stack; a stateless single-node,
  single-process execution engine; and a CLI tool for driving that engine.
- **dagit**: Dagit is a rich viewer for Dagster assets, including a DAG browser, a type-aware
  config editor, and a streaming execution interface.
- **dagster-ge**: A Dagster integration with Great Expectations. (see
  https://github.com/great-expectations/great_expectations)
- **dagstermill**: An experimental prototype for integrating productionized notebooks into
  dagster pipelines. Built on the papermill library (https://github.com/nteract/papermill).
- **dagster-contrib**: A growing library of components for using Dagster with common data
  tools like Pandas and SQLAlchemy, along with worked examples.
- **airline-demo**: A substantial demo project illustrating how these tools can be used together
  to manage a realistic data pipeline.
- **js_modules/dagit** - a web app that is a ui for dagit

Go to https://dagster.readthedocs.io/en/latest/ for complete documentation, including a
step-by-step tutorial and notes on the demo project.

For details on contributing or running the project for development, see
https://dagster.readthedocs.io/en/latest/contributing.html.
