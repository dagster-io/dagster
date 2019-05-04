.. image:: https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png
   :align: center

.. docs-include

.. image:: https://badge.fury.io/py/dagster.svg
   :target: https://badge.fury.io/py/dagster
.. image:: https://coveralls.io/repos/github/dagster-io/dagster/badge.svg?branch=master
   :target: https://coveralls.io/github/dagster-io/dagster?branch=master
.. image:: https://badge.buildkite.com/888545beab829e41e5d7303db15525a2bc3b0f0e33a72759ac.svg?branch=master
   :target: https://buildkite.com/dagster/dagster
.. image:: https://readthedocs.org/projects/dagster/badge/?version=master
   :target: https://dagster.readthedocs.io/en/master/

============
Introduction
============

Dagster is a system for building modern data applications. Combining an elegant programming model and beautiful tools, Dagster allows infrastructure engineers, data engineers, and data scientists to seamlessly collaborate to process and produce the trusted, reliable data needed in today's world.

``pip install dagster dagit`` and jump immediately to our `tutorial <https://dagster.readthedocs.io/en/latest/sections/learn/tutorial/index.html>`_

Or read our `complete documentation <https://dagster.readthedocs.io>`_


For details on contributing or running the project for development, read `here <https://dagster.readthedocs.io/en/latest/sections/community/contributing.html>`_.

This repository contains a number of distinct subprojects.

Top Level Tools:

- **dagster**: The core programming model and abstraction stack; stateless, single-node,
  single-process and multi-process execution engines; and a CLI tool for driving those engines.
- **dagit**: A rich development environment for Dagster, including a DAG browser, a type-aware config editor,
  and a streaming execution interface.
- **dagstermill**: Built on the papermill library (https://github.com/nteract/papermill) Dagstermill is meant for integrating productionized Jupyter notebooks into dagster pipelines.
- **dagster-airflow**: Allows Dagster pipelines to be scheduled and executed, either containerized or uncontainerized, as Apache Airflow DAGs (https://github.com/apache/airflow)

Supporting Libraries:

- **libraries/dagster-aws**: Dagster solids and tools for interacting with Amazon Web Services.
- **libraries/dagster-ge**: A Dagster integration with Great Expectations. (see
  https://github.com/great-expectations/great_expectations)
- **dagster-pandas**: A Dagster integration with Pandas.
- **dagster-pyspark**: A Dagster integration with Pyspark.
- **dagster-snowflake**: A Dagster integration with Snowflake.
- **dagster-spark**: A Dagster integration with Spark.

Example Projects:

- **airline-demo**: A substantial demo project illustrating how these tools can be used together
  to manage a realistic data pipeline.
- **event-pipeline-demo**: A substantial demo project illustrating a typical web event processing
  pipeline with Spark and Scala.

Internal Libraries;

- **js_modules/dagit** - The web UI for dagit
- **dagster-graphql**: A GraphQL-based interface for interacting with the Dagster engines and
  repositories of Dagster pipelines.


Come join our slack!: https://tinyurl.com/dagsterslack
