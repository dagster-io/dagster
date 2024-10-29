#####################
Sigma (dagster-sigma)
#####################

Dagster allows you to represent your Sigma project as assets, alongside other your other
technologies like dbt and Sling. This allows you to see how your Sigma assets are connected to
your other data assets, and how changes to other data assets might impact your Sigma project.

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

.. autofunction:: load_sigma_asset_specs
