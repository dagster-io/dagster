#####################
dagster-sigma library
#####################

Dagster allows you to represent the workbooks and datasets in your Sigma project as assets alongside other
technologies including dbt and Sling. This allows you to visualize relationships between your Sigma assets
and their dependencies.


Related documentation pages: `Using Dagster with Sigma <https://docs.dagster.io/integrations/libraries/sigma>`_.

.. currentmodule:: dagster_sigma

*********
Component
*********

.. autoclass:: SigmaComponent
    :members:

To use the Sigma component, see the `Sigma component integration guide <https://docs.dagster.io/integrations/libraries/sigma>`_.

YAML configuration
==================

When you scaffold a Sigma component definition, the following ``defs.yaml`` configuration file will be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/guides/components/integrations/sigma-component/6-populated-component.yaml
    :language: yaml

*********
Sigma API
*********

Here, we provide interfaces to manage Sigma projects using the Sigma API.

Assets (Sigma API)
==================

.. autoclass:: SigmaOrganization

.. autoclass:: SigmaBaseUrl

.. autoclass:: DagsterSigmaTranslator

.. autoclass:: SigmaDataset

.. autoclass:: SigmaWorkbook

.. autoclass:: SigmaFilter

.. autofunction:: load_sigma_asset_specs
