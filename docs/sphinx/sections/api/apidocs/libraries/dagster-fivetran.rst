Fivetran (dagster-fivetran)
###########################

This library provides a Dagster integration with `Fivetran <https://www.fivetran.com>`_.

.. currentmodule:: dagster_fivetran

************************
FivetranAccountComponent
************************

.. autoclass:: FivetranAccountComponent

To use the Fivetran component, see the `Fivetran component integration guide <https://docs.dagster.io/integrations/libraries/fivetran>`_.

Component YAML
==============

When you scaffold a Fivetran component definition, the following ``defs.yaml`` configuration file will be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/5-component.yaml
    :language: yaml

*********************
Assets (Fivetran API)
*********************

.. autoclass:: FivetranWorkspace

.. autoclass:: DagsterFivetranTranslator

.. autodecorator:: fivetran_assets

.. autofunction:: load_fivetran_asset_specs

.. autofunction:: build_fivetran_assets_definitions

.. autoclass:: dagster_fivetran.fivetran_event_iterator.FivetranEventIterator

.. autoclass:: ConnectorSelectorFn

******
Legacy
******

.. autoconfigurable:: fivetran_resource
    :annotation: ResourceDefinition

.. autoconfigurable:: FivetranResource
    :annotation: ResourceDefinition

.. autofunction:: load_assets_from_fivetran_instance

.. autofunction:: build_fivetran_assets

.. autoconfigurable:: fivetran_sync_op