Power BI (dagster-powerbi)
##########################

Dagster allows you to represent your Power BI Workspaces as assets, alongside other your other
technologies like dbt and Sling. This allows you to see how your Power BI assets are connected to
your other data assets, and how changes to other data assets might impact your Power BI Workspaces.

.. currentmodule:: dagster_powerbi

*********
Component
*********

.. autoclass:: PowerBIWorkspaceComponent

To use the Power BI component, see the `Power BI component integration guide <https://docs.dagster.io/integrations/libraries/powerbi>`_.

YAML configuration
==================

When you scaffold a Power BI component definition, the following ``defs.yaml`` configuration file will be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/6-populated-component.yaml
    :language: yaml

*********************
Assets (Power BI API)
*********************

Here, we provide interfaces to manage Power BI Workspaces using the Power BI API.


.. autoclass:: PowerBIServicePrincipal

.. autoclass:: PowerBIToken

.. autoclass:: PowerBIWorkspace

.. autoclass:: DagsterPowerBITranslator

.. autofunction:: load_powerbi_asset_specs

.. autofunction:: build_semantic_model_refresh_asset_definition
