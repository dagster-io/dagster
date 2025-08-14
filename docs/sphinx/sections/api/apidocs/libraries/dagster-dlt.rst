dlt (dagster-dlt)
-----------------

This library provides a Dagster integration with `dlt <https://dlthub.com>`_.

For more information on getting started, see the `Dagster & dlt <https://docs.dagster.io/integrations/libraries/dlt>`_ documentation.


.. currentmodule:: dagster_dlt

dlt component YAML configuration
=====================================

To use the Fivetran component, see the `dlt component integration guide <https://docs.dagster.io/integrations/libraries/dlt>`_.

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/integrations/dlt/defs.yaml


Assets
======

.. autodecorator:: dlt_assets

.. autofunction:: build_dlt_asset_specs

.. autoclass:: DagsterDltTranslator

Resources
=========

.. autoclass:: DagsterDltResource
    :members: run
