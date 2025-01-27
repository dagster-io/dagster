Airbyte (dagster-airbyte)
---------------------------

This library provides a Dagster integration with `Airbyte <https://www.airbyte.com/>`_.

For more information on getting started, see the `Airbyte integration guide <https://docs.dagster.io/integrations/airbyte>`_.

.. currentmodule:: dagster_airbyte


Assets (Airbyte API)
====================

.. autoclass:: AirbyteCloudWorkspace

.. autoclass:: DagsterAirbyteTranslator

.. autofunction:: load_airbyte_cloud_asset_specs

.. autodecorator:: airbyte_assets

.. autofunction:: build_airbyte_assets_definitions


Legacy
======

.. autoconfigurable:: AirbyteResource
    :annotation: ResourceDefinition

.. autofunction:: load_assets_from_airbyte_instance

.. autofunction:: build_airbyte_assets

.. autoconfigurable:: airbyte_sync_op
