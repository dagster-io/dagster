#######################
Looker (dagster-looker)
#######################

Dagster allows you to represent your Looker project as assets, alongside other your other
technologies like dbt and Sling. This allows you to see how your Looker assets are connected to
your other data assets, and how changes to other data assets might impact your Looker project.

.. currentmodule:: dagster_looker

*********
Component
*********

.. autoclass:: LookerComponent
    :members:

To use the Looker component, see the `Looker component integration guide <https://docs.dagster.io/integrations/libraries/looker>`_.

YAML configuration
==================

When you scaffold a Looker component definition, the following ``defs.yaml`` configuration file will be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/guides/components/integrations/looker-component/6-populated-component.yaml
    :language: yaml

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

.. autoclass:: LookerFilter

.. autofunction:: load_looker_asset_specs

.. autofunction:: build_looker_pdt_assets_definitions

*************
lkml (LookML)
*************

Here, we provide interfaces to manage Looker projects defined a set of locally accessible
LookML files.

Assets (lkml)
=============

.. autofunction:: build_looker_asset_specs

.. autoclass:: DagsterLookerLkmlTranslator
