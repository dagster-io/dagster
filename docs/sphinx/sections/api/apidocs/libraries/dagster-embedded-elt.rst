####################################
embedded-elt (dagster-embedded-elt)
####################################

This package provides a framework for building ELT pipelines with Dagster through
helpful pre-built assets and resources.

This package currently includes a `Sling <https://slingdata.io>`_ integration which
provides a simple way to sync data between databases and file systems.

Related documentation pages: `embedded-elt </integrations/embedded-elt>`_.


******
Sling
******

.. currentmodule:: dagster_embedded_elt.sling

Assets
======

.. autofunction:: build_sling_asset

Resources
=========

.. autoclass:: SlingResource
   :members: sync

.. autoclass:: dagster_embedded_elt.sling.resources.SlingSourceConnection
.. autoclass:: dagster_embedded_elt.sling.resources.SlingTargetConnection
