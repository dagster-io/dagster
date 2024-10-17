#####################
Sigma (dagster-sigma)
#####################

Dagster allows you to represent your Sigma project as assets, alongside other your other
technologies like dbt and Sling. This allows you to see how your Sigma assets are connected to
your other data assets, and how changes to other data assets might impact your Looker project.

.. currentmodule:: dagster_sigma

**********
Looker API
**********

Here, we provide interfaces to manage Looker projects using the Looker API.

Assets (Looker API)
===================

.. autoclass:: SigmaOrganization

.. autoclass:: SigmaBaseUrl

.. autoclass:: DagsterSigmaTranslator

.. autoclass:: SigmaDataset

.. autoclass:: SigmaWorkbook
