#######################
Looker (dagster-looker)
#######################

Dagster allows you to represent your Looker project as assets, alongside other your other
technologies like dbt and Sling. This allows you to see how your Looker assets are connected to
your other data assets, and how changes to other data assets might impact your Looker project.

.. currentmodule:: dagster_looker


Assets
======

.. autofunction:: build_looker_asset_specs

.. autoclass:: DagsterLookerLkmlTranslator
