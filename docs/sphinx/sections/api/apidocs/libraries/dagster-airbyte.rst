Airbyte (dagster-airbyte)
---------------------------

This library provides a Dagster integration with `Airbyte <https://www.airbyte.com/>`_.

For more information on getting started, see the `Airbyte integration guide </integrations/airbyte>`_.

.. currentmodule:: dagster_airbyte

Ops
===

.. autoconfigurable:: airbyte_sync_op


Resources
=========

.. autoconfigurable:: airbyte_resource
    :annotation: ResourceDefinition

.. autoclass:: AirbyteResource
    :members:

Assets
======

.. autofunction:: load_assets_from_airbyte_instance

.. autofunction:: load_assets_from_airbyte_project

.. autofunction:: build_airbyte_assets