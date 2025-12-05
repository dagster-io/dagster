#########################
Tableau (dagster-tableau)
#########################

Dagster allows you to represent your Tableau workspace as assets, alongside other your other
technologies like dbt and Sling. This allows you to see how your Tableau assets are connected to
your other data assets, and how changes to other data assets might impact your Tableau workspace.

.. currentmodule:: dagster_tableau

*********
Component
*********

.. autoclass:: TableauComponent
    :members:

To use the Tableau component, see the `Tableau component integration guide <https://docs.dagster.io/integrations/libraries/tableau>`_.

YAML configuration
==================

When you scaffold a Tableau component definition, the following ``defs.yaml`` configuration file will be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/guides/components/integrations/tableau-component/6-populated-component.yaml
    :language: yaml

***********
Tableau API
***********

Here, we provide interfaces to manage Tableau projects using the Tableau API.

Assets (Tableau API)
====================

.. autoclass:: TableauCloudWorkspace

.. autoclass:: TableauServerWorkspace

.. autoclass:: DagsterTableauTranslator

.. autodecorator:: tableau_assets

.. autofunction:: load_tableau_asset_specs

.. autofunction:: build_tableau_materializable_assets_definition

.. autofunction:: parse_tableau_external_and_materializable_asset_specs
