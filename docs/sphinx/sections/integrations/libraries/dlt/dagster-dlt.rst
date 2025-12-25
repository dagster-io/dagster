dagster-dlt library
###################

This library provides a Dagster integration with `dlt <https://dlthub.com>`_.

For more information on getting started, see the `Dagster & dlt <https://docs.dagster.io/integrations/libraries/dlt>`_ documentation.


.. currentmodule:: dagster_dlt

*********
Component
*********

.. autoclass:: DltLoadCollectionComponent
    :members:

To use the dlt component, see the `dlt component integration guide <https://docs.dagster.io/integrations/libraries/dlt>`_.

YAML configuration
==================

When you scaffold a dlt component definition, the following ``defs.yaml`` configuration file will be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/guides/components/integrations/dlt-component/6-defs.yaml
    :language: yaml

******
Assets
******

.. autodecorator:: dlt_assets

.. autofunction:: build_dlt_asset_specs

.. autoclass:: DagsterDltTranslator

*********
Resources
*********

.. autoclass:: DagsterDltResource
    :members: run
