Dagster packages
----------------

Core packages
=============

Dagster is a highly componentized system built around a few core packages:

**dagster**
  Contains the core programming model, which you'll use to write solids, pipelines, and all the
  other components of a data application, as well as the ``dagster`` CLI tool for executing and
  managing pipelines. Every Dagster project starts here and will import from the public API of this
  library.

**dagit**
  Our GUI tool for visualizing, testing, scheduling, running, and monitoring Dagster pipelines,
  written against the GraphQL API. You'll use Dagit locally to develop and monitor pipelines, as
  well as in production for long-running deployments.

**dagster-graphql**
  Defines a `GraphQL <https://graphql.org/>`_ API for executing pipelines and includes a CLI tool
  for executing queries against the API. Users will typically not make imports from this package,
  but tools like Dagit, integrations like dagster-airflow, and some containerization strategies are
  all built on the GraphQL API. Most users should not install this package directly

Libraries
=========

Dagster also provides a growing set of optional add-on libraries to integrate with infrastructure and
other components of the data ecosystem. These libraries vary in maturity and are under active
development as the community surfaces its needs.

We distinguish between "beta" and "experimental" libraries as a rough indication of the
production-readiness of these libraries, and we are always excited to identify new design partners
and collaborators interested in pushing their capabilities forwards.

As a rule, beta libraries are ready for real use, but subject to change at a faster rate than the
core libraries. In particular, breaking changes in public APIs may not be limited to minor releases.

Experimental libraries are exploratory and the functionality they expose may not be complete or
ready for production.

If you are working on a library that helps Dagster interact with another part of the data ecosystem,
please reach out to us. We welcome external contributions and have already incorporated experimental
libraries from the community (dagster-github).

Beta
~~~~

**dagster-airflow**
  Enables incremental adoption of Dagster in existing `Apache Airflow <https://airflow.apache.org/>`_
  environments with a facility for compiling dagster pipelines to Airflow DAGs. Not recommended for
  greenfield installations.

**dagster-aws**
  Tools for working with `Amazon Web Services <https://aws.amazon.com/>`_, including custom
  Cloudwatch loggers, EMR for hosted cluster compute, and S3 for persistent storage of logs and
  intermediate artifacts. Includes a CLI tool for easy-up/proof-of-concept deployment of hosted
  dagit to AWS. S3 and GCS are the preferred persistence solutions for long-running deploys.

**dagster-celery**
  Pluggable executor to run Dagster pipelines using the
  `Celery task queue <http://www.celeryproject.org/>`_, including a CLI tool for managing worker
  processes. Preferred parallel execution solution for long-running deploys.

**dagster-cron**
  Uses system cron to enable scheduled pipeline runs, integrated with Dagit. (Does not support
  Windows.) Preferred scheduling solution.

**dagster-gcp**
  Tools for working with `Google Cloud Platform <https://cloud.google.com/>`_, including BigQuery
  databases and Dataproc for hosted cluster compute, as well as GCS for persistent storage of logs
  and intermediate artifacts. S3 and GCS are the preferred persistence solutions for long-running
  deploys.

**dagster-k8s**
  Model Helm chart for deploying Dagster on Kubernetes, as well as a pluggable Kubernetes-aware
  run launcher. Preferred deployment solution for long-running deploys.

**dagstermill**
  Wraps `Jupyter <https://jupyter.org/>`_ notebooks as solids to enable repeatable
  execution integrated into and interoperating with Dagster pipelines, as well as interaction with
  the Dagster environment during notebook development. Built on
  `papermill <https://github.com/nteract/papermill>`_

**dagster-pandas**
  Tools for working with the common `Pandas <https://pandas.pydata.org/>`_ library for Python data
  frames, including custom type definition with arbitrary columnar or dataframe-wide semantic
  constraints.

**dagster-postgres**
  Pluggable Postgres-backed storage for run history and event logs, allowing Dagit and other dagster
  tools to point at shared remote databases. Preferred storage solution for long-running deploys.

Experimental
~~~~~~~~~~~~

**dagster-bash**
  Library solids to execute bash commands.

**dagster-dask**
  Pluggable executor to run Dagster pipelines using the `Dask <https://dask.org/>`_ framework for
  parallel computing.

**dagster-datadog**
  Library resources for reporting metrics to `Datadog <https://www.datadoghq.com/product/>`_ from
  within Dagster pipelines.

**dagster-dbt**
  Library solids to wrap invocations of `dbt <https://www.getdbt.com/>`_ and integrate with Dagster
  pipelines.

**dagster-ge**
  Tools for working with the `Great Expectations <https://greatexpectations.io/>`_ data quality
  testing library.

**dagster-github**
  Library resource to interact with `Github <https://github.com/>`_ from within Dagster pipelines.

**dagster-pagerduty**
  Library resource to trigger `PagerDuty <https://www.pagerduty.com/>`_ alerts from within Dagster
  pipelines.

**dagster-papertrail**
  Custom logger using `Papertrail <https://papertrailapp.com/>`_.

**dagster-prometheus**
  Library resource for reporting metrics to `Prometheus <https://prometheus.io/>`_ from within
  Dagster pipelines.

**dagster-pyspark**
  Library solid factory, resources, and custom data types for working with
  `PySpark <https://spark.apache.org/docs/latest/api/python/index.html>`_ in Dagster pipelines.

**dagster-slack**
  Library resource to post to `Slack <https://slack.com/>`_ from within Dagster pipelines.

**dagster-snowflake**
  Library solids and resources for connecting to and querying
  `Snowflake <https://www.snowflake.com/>`_ data warehouses.

**dagster-spark**
  Library solid factory, resources, and data types for working with
  `Spark <https://spark.apache.org/>`_ clusters and jobs.

**dagster-ssh**
  Library resources and solids for SSH and SFTP execution.

**dagster-twilio**
  Library resource that makes a `Twilio <https://www.twilio.com/>`_ client available to Dagster
  pipelines.

Each of these packages is published to PyPI and installable using ``pip``. Code is also
`available on Github <https://github.com/dagster-io/dagster>`_ in a monorepo. We welcome
issues, pull requests, and new library `contributions <../community/contributing.html>`_.
