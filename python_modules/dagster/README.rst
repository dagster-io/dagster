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
.. image:: https://img.shields.io/pypi/l/dagster.svg
   :target: http://www.apache.org/licenses/LICENSE-2.0.txt
.. image:: https://img.shields.io/pypi/pyversions/dagster.svg
   :target: https://pypi.org/project/dagster/

============
Introduction
============

Dagster is an opinionated system and programming model for data pipelines. This process goes by
many names -- ETL (extract-transform-load), ELT (extract-load-transform), model production, data
integration, and so on -- but in essence they all describe the same activity: performing a set of
computations structured as a DAG (directed, acyclic graph) that end up producing data assets,
whether those assets be tables, files, machine-learning models, etc.

This project contains the core programming model and abstraction stack behind Dagster; a stateless
single-node, single-process execution engine; and a CLI tool for driving that engine.

Go to https://dagster.readthedocs.io/ for complete documentation, including a
step-by-step tutorial and notes on the demo project.

For details on contributing or running the project for development, see
https://dagster.readthedocs.io/en/latest/contributing.html.
