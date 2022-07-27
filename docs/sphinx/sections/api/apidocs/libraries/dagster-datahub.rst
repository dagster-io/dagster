Datahub (dagster-datahub)
-------------------------

This library provides an integration with Datahub, to support pushing metadata to Datahub from
within Dagster ops.

|

We use the `Datahub Python Library <https://github.com/datahub-project/datahub>`_. To use it, you'll
first need to start up a Datahub Instance. `Datahub Quickstart Guide
<https://datahubproject.io/docs/quickstart>`_.

|

.. currentmodule:: dagster_datahub

.. autoconfigurable:: datahub_rest_emitter
  :annotation: ResourceDefinition

.. autoconfigurable:: datahub_kafka_emitter
  :annotation: ResourceDefinition
