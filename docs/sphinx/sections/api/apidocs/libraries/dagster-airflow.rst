Airflow (dagster-airflow)
-------------------------

This library provides a Dagster integration with `Airflow <https://github.com/apache/airflow>`_.

For more information on getting started, see the `Airflow integration guide </integrations/airflow>`_.

.. currentmodule:: dagster_airflow

Run Airflow on Dagster
======================

.. autofunction:: make_dagster_definitions_from_airflow_dags_path

.. autofunction:: make_dagster_definitions_from_airflow_dag_bag

.. autofunction:: make_schedules_and_jobs_from_airflow_dag_bag

.. autofunction:: make_dagster_job_from_airflow_dag

.. autofunction:: load_assets_from_airflow_dag


Orchestrate Dagster from Airflow
================================

.. autoclass:: DagsterCloudOperator

.. autoclass:: DagsterOperator