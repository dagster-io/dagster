#######################
Looker (dagster-looker)
#######################

Dagster allows you to represent your Looker project as assets, alongside other your other
technologies like dbt and Sling. This allows you to see how your Looker assets are connected to
your other data assets, and how changes to other data assets might impact your Looker project.

.. currentmodule:: dagster_looker

**********
Looker API
**********

Here, we provide interfaces to manage Looker projects using the Looker API.

Assets (Looker API)
===================

.. autoclass:: LookerResource

.. autoclass:: DagsterLookerApiTranslator

.. autoclass:: LookerStructureData

.. autoclass:: LookerStructureType

.. autoclass:: RequestStartPdtBuild

*************
lkml (LookML)
*************

Here, we provide interfaces to manage Looker projects defined a set of locally accessible
LookML files.

Assets (lkml)
=============

.. autofunction:: build_looker_asset_specs

.. autoclass:: DagsterLookerLkmlTranslator
