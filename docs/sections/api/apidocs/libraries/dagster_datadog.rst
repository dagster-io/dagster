Datadog (dagster_datadog)
-------------------------

This library provides an integration with Datadog, to support publishing metrics to Datadog from
within Dagster solids.

|

We use the Python `datadogpy <https://github.com/DataDog/datadogpy>`_ library. To use it, you'll
first need to create a DataDog account and get both `API and Application keys
<https://docs.datadoghq.com/account_management/api-app-keys/>`_.

|

The integration uses `DogStatsD <https://docs.datadoghq.com/developers/dogstatsd/>`_, so you'll need
to ensure the datadog agent is running on the host you're sending metrics from.


.. currentmodule:: dagster_datadog

.. autodata:: datadog_resource
  :annotation: ResourceDefinition
