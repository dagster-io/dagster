dagster-sling library
#####################

This library provides a Dagster integration with `Sling <https://slingdata.io>`_.

For more information on getting started, see the `Dagster & Sling <https://docs.dagster.io/integrations/libraries/sling>`_ documentation.


.. currentmodule:: dagster_sling

*********
Component
*********

.. autoclass:: SlingReplicationCollectionComponent
    :members:

To use the Sling component, see the `Sling component integration guide <https://docs.dagster.io/integrations/libraries/sling>`_.

YAML configuration
==================

When you scaffold a Sling component definition, the following ``defs.yaml`` configuration file will be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/guides/components/integrations/sling-component/5-component.yaml
    :language: yaml

The following ``replication.yaml`` file will also be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/guides/components/integrations/sling-component/6-replication.yaml
    :language: yaml

******
Assets
******

.. autodecorator:: sling_assets

.. autoclass:: DagsterSlingTranslator

*********
Resources
*********

.. autoclass:: SlingResource
    :members: replicate

.. autoclass:: SlingConnectionResource
