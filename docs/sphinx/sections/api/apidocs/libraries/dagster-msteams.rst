Microsoft Teams (dagster-msteams)
---------------------------------

.. currentmodule:: dagster_msteams

Resource
=========
.. autoconfigurable:: MSTeamsResource
  :annotation: ResourceDefinition

Sensors
========

.. autodata:: teams_on_failure
  :annotation: HookDefinition

.. autodata:: teams_on_success
  :annotation: HookDefinition

.. autofunction:: make_teams_on_run_failure_sensor


Legacy
======

.. autoconfigurable:: msteams_resource
  :annotation: ResourceDefinition
