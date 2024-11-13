#########################
PowerBI (dagster-powerbi)
#########################

Dagster allows you to represent your PowerBI Workspaces as assets, alongside other your other
technologies like dbt and Sling. This allows you to see how your PowerBI assets are connected to
your other data assets, and how changes to other data assets might impact your PowerBI Workspaces.

.. currentmodule:: dagster_powerbi

***********
PowerBI API
***********

Here, we provide interfaces to manage PowerBI Workspaces using the PowerBI API.

Assets (PowerBI)
================

.. autoclass:: PowerBIServicePrincipal

.. autoclass:: PowerBIToken

.. autoclass:: PowerBIWorkspace

.. autoclass:: DagsterPowerBITranslator

.. autofunction:: load_powerbi_asset_specs

.. autofunction:: build_semantic_model_refresh_asset_definition
