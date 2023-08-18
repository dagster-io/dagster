Fivetran (dagster-fivetran)
---------------------------

This library provides a Dagster integration with `Fivetran <https://www.fivetran.com/>`_.

.. currentmodule:: dagster_fivetran


Resources
=========

.. autoconfigurable:: FivetranResource
    :annotation: ResourceDefinition

Assets
======

.. autofunction:: load_assets_from_fivetran_instance

.. autofunction:: build_fivetran_assets


Ops
===

.. autoconfigurable:: fivetran_sync_op


Legacy
======

.. autoconfigurable:: fivetran_resource
    :annotation: ResourceDefinition
