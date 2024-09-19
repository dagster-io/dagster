PagerDuty (dagster-pagerduty)
-----------------------------

This library provides an integration with PagerDuty, to support creating alerts from your Dagster
code.


Presently, it provides a thin wrapper on the `Events API V2 <https://v2.developer.pagerduty.com/docs/events-api-v2>`_.

Getting Started
---------------

You can install this library with:

.. code-block::

   pip install dagster_pagerduty

To use this integration, you'll first need to create an Events API V2 PagerDuty integration on a PagerDuty service. There are instructions
`here <https://support.pagerduty.com/docs/services-and-integrations#section-events-api-v2>`_ for
creating a new PagerDuty service & integration.

Once your Events API V2 integration is set up, you'll find an Integration Key (also referred to as a
"Routing Key") on the Integrations tab for your service. This key is used to authorize events
created from the PagerDuty events API.

Once your service/integration is created, you can provision a PagerDuty resource and issue PagerDuty
alerts from within your ops.


.. currentmodule:: dagster_pagerduty

.. autoconfigurable:: PagerDutyService
  :annotation: ResourceDefinition


Legacy
=========

.. autoconfigurable:: pagerduty_resource
  :annotation: ResourceDefinition