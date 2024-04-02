####################################
embedded-elt (dagster-embedded-elt)
####################################

This package provides a framework for building ELT pipelines with Dagster through helpful pre-built
assets and resources.

This package currently includes a `Sling <https://slingdata.io>`_ integration which provides a
simple way to sync data between databases and file systems.

And a `dlt <https://dlthub.com>`_ integration which provides a way to load data from systems and
APIs.

Related documentation pages: `embedded-elt </integrations/embedded-elt>`_.

.. currentmodule:: dagster_embedded_elt.sling

***************************
dagster-embedded-elt.sling
***************************

Assets (Sling)
==============

.. autodecorator:: sling_assets

.. autoclass:: DagsterSlingTranslator

Resources (Sling)
=================

.. autoclass:: SlingResource
    :members: sync, replicate

.. autoclass:: SlingConnectionResource

Deprecated
-----------

.. autofunction:: build_sling_asset
.. autoclass:: dagster_embedded_elt.sling.resources.SlingSourceConnection
.. autoclass:: dagster_embedded_elt.sling.resources.SlingTargetConnection

.. currentmodule:: dagster_embedded_elt.dlt

***************************
dagster-embedded-elt.dlt
***************************

Assets (dlt)
==============

.. autodecorator:: dlt_assets

.. autoclass:: DagsterDltTranslator

Resources (dlt)
=================

.. autoclass:: DagsterDltResource
    :members: run
