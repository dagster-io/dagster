.. _deployment-gcp:

GCP Deployment
--------------

.. rubric:: Compute Engine hosted Dagit

To host dagit on a bare VM or in Docker on ECS, see the `Local or Standalone Dagit <local.html>`_
guide.

.. rubric:: Execution

Out of the box, Dagster runs single-process execution. To enable multi-process execution, add the
following to your pipeline configuration YAML:

.. code-block:: yaml

    :caption: execution_config.yaml

    execution:
      multiprocess:
        max_concurrent: 0
    storage:
      filesystem:


.. rubric:: Run / Events Storage

We recommend launching a Cloud SQL PostgreSQL instance for run and events data. You should then
configure Dagit to use Cloud SQL; as noted previously, this can be accomplished by adding the
following to ``$DAGSTER_HOME/dagster.yaml``:

.. code-block:: yaml

   :caption: dagster.yaml

    run_storage:
        module: dagster_postgres.run_storage
        class: PostgresRunStorage
        config:
            postgres_url: "postgresql://{username}:{password}@{host}:5432/{database}"

    event_log_storage:
        module: dagster_postgres.event_log
        class: PostgresEventLogStorage
        config:
            postgres_url: "postgresql://{username}:{password}@{host}:5432/{database}"


In this case, you'll want to ensure you provide the right connection strings for your Cloud SQL
instance, and that the node or container hosting Dagit is able to connect to RDS.

.. rubric:: GCS Intermediates Storage

You'll also want to configure a GCS bucket to use for Dagster intermediates (see the `intermediates
tutorial guide <../tutorial/intermediates.html>`_ for more info). Dagster supports serializing data
passed between solids to GCS; to enable this, you need to add S3 storage to your
:py:class:`ModeDefinition`:

.. code-block:: python

    from dagster_gcp.gcs.system_storage import gcs_plus_default_storage_defs
    from dagster import ModeDefinition

    prod_mode = ModeDefinition(name='prod', system_storage_defs=gcs_plus_default_storage_defs)


Then, just add the following YAML to your pipeline config:

.. code-block:: yaml

    :caption: execution_config.yaml

    storage:
      gcs:
        config:
          gcs_bucket: your-s3-bucket-name

With this in place, your pipeline runs will store intermediates on GCS in the location
``gs://<bucket>/dagster/storage/<pipeline run id>/intermediates/<solid name>.compute``
