Sling (dagster-sling)
---------------------

This library provides a Dagster integration with `Sling <https://slingdata.io>`_.

For more information on getting started, see the `Dagster & Sling <https://docs.dagster.io/integrations/libraries/sling>`_ documentation.


.. currentmodule:: dagster_sling

Sling component YAML
====================

To use the Sling component, see the `Sling component integration guide <https://docs.dagster.io/integrations/libraries/sling>`_.

When you run ``dg scaffold defs dagster_sling.SlingReplicationCollectionComponent SLING_DEFINITIONS_FOLDER``, the following ``defs.yaml`` configuration file will be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/integrations/sling/defs.yaml

The following ``replication.yaml`` file will also be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/integrations/sling/replication.yaml

Assets
======

.. autodecorator:: sling_assets

.. autoclass:: DagsterSlingTranslator

Resources
=========

.. autoclass:: SlingResource
    :members: replicate

.. autoclass:: SlingConnectionResource
