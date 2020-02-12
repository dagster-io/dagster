dagster_celery
---------------

.. currentmodule:: dagster_celery

.. autodata:: celery_executor
  :annotation: ExecutorDefinition

CLI
^^^

The ``dagster-celery`` CLI lets you start, monitor, and terminate workers.

.. click:: dagster_celery.cli:worker_start_command
   :prog: dagster-celery worker start

.. click:: dagster_celery.cli:worker_list_command
   :prog: dagster-celery worker list

.. click:: dagster_celery.cli:worker_terminate_command
   :prog: dagster-celery worker terminate
