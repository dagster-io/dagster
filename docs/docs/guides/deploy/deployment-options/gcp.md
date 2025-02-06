---
title: "Deploying Dagster to Google Cloud Platform"
description: To deploy Dagster to GCP, Google Compute Engine (GCE) can host the Dagster webserver, Google Cloud SQL can store runs and events, and Google Cloud Storage (GCS) can act as an IO manager.
sidebar_position: 60
---

To deploy Dagster to GCP, Google Compute Engine (GCE) can host the Dagster webserver, Google Cloud SQL can store runs and events, and Google Cloud Storage (GCS) can act as an IO manager.

## Hosting the Dagster webserver or Dagster Daemon on GCE

To host the Dagster webserver or Dagster daemon on a bare VM or in Docker on GCE, see [Running Dagster as a service](/guides/deploy/deployment-options/deploying-dagster-as-a-service).

## Using Cloud SQL for run and event log storage

We recommend launching a Cloud SQL PostgreSQL instance for run and events data. You can configure the webserver to use Cloud SQL to run and events data by setting blocks in your `$DAGSTER_HOME/dagster.yaml` appropriately:

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster-pg.yaml" />

In this case, you'll want to ensure you provide the right connection strings for your Cloud SQL instance, and that the node or container hosting the webserver is able to connect to Cloud SQL.

Be sure that this file is present, and `_DAGSTER_HOME_` is set, on the node where the webserver is running.

Note that using Cloud SQL for run and event log storage does not require that the webserver be running in the cloud. If you are connecting a local webserver instance to a remote Cloud SQL storage, double check that your local node is able to connect to Cloud SQL.

## Using GCS for IO Management

You'll probably also want to configure a GCS bucket to store op outputs via persistent [IO Managers](/guides/build/io-managers/). This enables reexecution, review and audit of op outputs, and cross-node cooperation (e.g., with the <PyObject section="execution" module="dagster" object="multiprocess_executor" /> or <PyObject section="libraries" module="dagster_celery" object="celery_executor" />).

You'll first need to need to create a job using <PyObject section="libraries" module="dagster_gcp" object="gcs_pickle_io_manager"/> as its IO Manager (or [define a custom IO Manager](/guides/build/io-managers/defining-a-custom-io-manager)):

<CodeExample path="docs_snippets/docs_snippets/deploying/gcp/gcp_job.py" />

With this in place, your job runs will store outputs on GCS in the location `gs://<bucket>/dagster/storage/<job run id>/files/<op name>.compute`.
