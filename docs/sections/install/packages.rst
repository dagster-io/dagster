Dagster packages
----------------

Dagster is a highly componentized system consisting of a number of core packages.

    - **dagster** contains the core programming model and the ``dagster`` CLI tool for executing
      and managing pipelines.
    - **dagster-graphql** defines a `GraphQL <https://graphql.org/>`_ API for executing and managing
      pipelines and their outputs and includes a CLI tool for executing queries against the API.
    - **dagit** is our powerful GUI tool for exploring, managing, scheduling, and monitoring
      dagster pipelines, written against the GraphQL API.
    - **dagster-airflow** provides a facility for compiling dagster pipelines to Airflow DAGs so
      that they can be scheduled and orchestrated using `Apache Airflow <https://airflow.apache.org/>`_.
    - **dagster-dask** provides a pluggable execution engine for dagster pipelines so they can be
      executed using the `Dask <https://dask.org/>`_ framework for parallel computing.
    - **dagstermill** provides the ability to wrap `Jupyter <https://jupyter.org/>`_ notebooks as
      dagster solids for repeatable execution as part of dagster pipelines.

Dagster also provides a large set of optional add-on libraries that integrate with other parts of
the data ecosystem.

    - **dagster-aws** includes facilities for working with
      `Amazon Web Services <https://aws.amazon.com/>`_, including Cloudwatch for logging, EMR for
      hosted cluster compute, S3 for persistent storage of logs and intermediate artifacts, and
      a CLI tool to streamline deployment of hosted dagit to AWS.
    - **dagster-bash** includes library solids to execute bash commands.
    - **dagster-cron** includes a simple scheduler that integrates with dagit, built on cron.
    - **dagster-datadog** includes a resource wrapping the dogstatsd library for reporting
      metrics to `Datadog <https://www.datadoghq.com/product/>`_.
    - **dagster-dbt** includes library solids to wrap invocations of
      `dbt <https://www.getdbt.com/>`_.
    - **dagster-gcp** includes facilities for working with
      `Google Cloud Platform <https://cloud.google.com/>`_, including BigQuery databases and
      Dataproc for hosted cluster compute.
    - **dagster-ge** includes tools for working with the
      `Great Expectations <https://greatexpectations.io/>`_ data quality testing library.
    - **dagster-github** includes a resource that lets you interact with `Github <https://github.com/>`_
      from within dagster pipelines.
    - **dagster-pagerduty** includes a resource that lets you trigger
      `PagerDuty <https://www.pagerduty.com/>`_ alerts from within dagster pipelines.
    - **dagster-pandas** includes tools for working with the common
      `Pandas <https://pandas.pydata.org/>`_ library for Python data frames.
    - **dagster-papertrail** includes facilities for logging to
      `Papertrail <https://papertrailapp.com/>`_.
    - **dagster-postgres** includes pluggable Postgres-backed storage for run history and event
      logs, allowing dagit and other dagster tools to point at shared remote databases. 
    - **dagster-pyspark** includes datatypes for working with
      `PySpark <https://spark.apache.org/docs/latest/api/python/index.html>`_ data frames in
      dagster pipelines.
    - **dagster-slack** includes a resource that lets you post to `Slack <https://slack.com/>`_
      from within dagster pipelines.
    - **dagster-snowflake** includes resources and solids for connecting to and querying
      `Snowflake <https://www.snowflake.com/>`_ data warehouses.
    - **dagster-spark** includes solids for working with `Spark <https://spark.apache.org/>`_ jobs.
    - **dagster-ssh** includes resources and solids for SSH and SFTP execution.
    - **dagster-twilio** includes a resource that makes a `Twilio <https://www.twilio.com/>`_
      client available within dagster pipelines.
