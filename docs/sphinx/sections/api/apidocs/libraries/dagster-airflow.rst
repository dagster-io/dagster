Airflow (dagster-airflow)
-------------------------

This library provides a Dagster integration with `Airflow <https://github.com/apache/airflow>`_.

For more information on getting started, see the `Airflow integration guide </integrations/airflow>`_.

.. currentmodule:: dagster_airflow

Run Airflow on Dagster
======================

.. autofunction:: make_dagster_job_from_airflow_dag

.. autofunction:: make_dagster_repo_from_airflow_dags_path

.. autofunction:: make_dagster_repo_from_airflow_dag_bag

.. autofunction:: make_dagster_repo_from_airflow_example_dags

.. autofunction:: airflow_operator_to_op


Run Dagster on Airflow
======================

.. autofunction:: make_airflow_dag

.. autofunction:: make_airflow_dag_for_operator

.. autofunction:: make_airflow_dag_containerized


Orchestrate Dagster from Airflow
================================

.. autofunction:: DagsterCloudOperator

.. autofunction:: DagsterOperator