#####################
Sigma (dagster-sigma)
#####################

Dagster allows you to represent the workbooks and datasets in your Sigma project as assets alongside other
technologies including dbt and Sling. This allows you to visualize relationships between your Sigma assets
and their dependencies.


Related documentation pages: `Using Dagster with Sigma <https://docs.dagster.io/integrations/sigma>`_.

.. currentmodule:: dagster_sigma

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
