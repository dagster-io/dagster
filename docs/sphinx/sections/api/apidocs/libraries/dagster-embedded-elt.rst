Embedded ELT (dagster-embedded-elt)
-----------------------------------

This package provides a framework for building ELT pipelines with Dagster through helpful pre-built
assets and resources. This package currently includes the following integrations:

* `Sling <https://slingdata.io>`_, which provides a simple way to sync data between databases and file systems

* `dlt <https://dlthub.com>`_, or data load tool, which provides a way to load data from systems and APIs

For more information on getting started, see the `Embedded ELT <https://docs.dagster.io/integrations/embedded-elt>`_ documentation.

----

**********************************
Sling (dagster-embedded-elt.sling)
**********************************

Refer to the `Sling guide <https://docs.dagster.io/integrations/embedded-elt/sling>`_ to get started.

.. currentmodule:: dagster_embedded_elt.sling

Assets (Sling)
==============

.. autodecorator:: sling_assets

.. autoclass:: DagsterSlingTranslator

Resources (Sling)
=================

.. autoclass:: SlingResource
    :members: replicate

.. autoclass:: SlingConnectionResource

----

*******************************
dlt (dagster-embedded-elt.dlt)
*******************************

Refer to the `dlt guide <https://docs.dagster.io/integrations/embedded-elt/dlt>`_ to get started.

.. currentmodule:: dagster_embedded_elt.dlt

Assets (dlt)
=================

.. autodecorator:: dlt_assets

.. autofunction:: build_dlt_asset_specs

.. autoclass:: DagsterDltTranslator

Resources (dlt)
=================

.. autoclass:: DagsterDltResource
    :members: run
