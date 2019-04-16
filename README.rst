.. image:: https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png
   :align: center

.. docs-include

.. image:: https://badge.fury.io/py/dagster.svg
   :target: https://badge.fury.io/py/dagster
.. image:: https://coveralls.io/repos/github/dagster-io/dagster/badge.svg?branch=master
   :target: https://coveralls.io/github/dagster-io/dagster?branch=master
.. image:: https://circleci.com/gh/dagster-io/dagster.svg?style=svg
   :target: https://circleci.com/gh/dagster-io/dagster
.. image:: https://readthedocs.org/projects/dagster/badge/?version=master
   :target: https://dagster.readthedocs.io/en/master/

============
Introduction
============

Dagster is a system for building modern data applications. Combining an elegant programming model and beautiful tools, Dagster allows infrastructure engineers, data engineers, and data scientists to seamlessly collaborate to process and produce the trusted, reliable data needed in today's world.

Go to https://dagster.readthedocs.io for complete documentation, including a
step-by-step tutorial and notes on the demo project.

For details on contributing or running the project for development, see
https://dagster.readthedocs.io/en/latest/contributing.html.

This repository contains a number of distinct subprojects:
 
- **dagster**: The core programming model and abstraction stack; stateless, single-node,
  single-process and multi-process execution engines; and a CLI tool for driving those engines.
- **dagster-graphql**: A GraphQL-based interface for interacting with the Dagster engines and
  repositories of Dagster pipelines.
- **dagit**: A rich viewer for Dagster assets, including a DAG browser, a type-aware config editor,
  and a streaming execution interface.

- **dagstermill**: An experimental prototype for integrating productionized Jupyter notebooks into
  dagster pipelines. Built on the papermill library (https://github.com/nteract/papermill).
- **dagster-airflow**: An experimental integration allowing Dagster pipelines to be scheduled and
  executed, either containerized or uncontainerized, as Apache Airflow DAGs (https://github.com/apache/airflow)


- **libraries/dagster-aws**: Dagster solids and tools for interacting with Amazon Web Services.
- **libraries/dagster-ge**: A Dagster integration with Great Expectations. (see
  https://github.com/great-expectations/great_expectations)
- **dagster-pandas**: A Dagster integration with Pandas.
- **dagster-pyspark**: A Dagster integration with Pyspark.
- **dagster-snowflake**: A Dagster integration with Snowflake.
- **dagster-spark**: A Dagster integration with Spark.
- **dagster-sqlalchemy**: A Dagster integration with SQLAlchemy.

- **airline-demo**: A substantial demo project illustrating how these tools can be used together
  to manage a realistic data pipeline.
- **event-pipeline-demo**: A substantial demo project illustrating a typical web event processing
  pipeline with Spark and Scala.

- **js_modules/dagit** - The web UI for dagit
