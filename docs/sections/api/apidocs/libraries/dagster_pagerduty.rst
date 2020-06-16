PagerDuty (dagster_pagerduty)
-----------------------------

This library provides an integration with PagerDuty, to support creating alerts from your Dagster
code.


Presently, it provides a thin wrapper on the `Events V2 API <https://v2.developer.pagerduty.com/docs/events-api-v2>`_.

Getting Started
---------------

You can install this library with:

.. code-block::

   pip install dagster_pagerduty

To use this integration, you'll first need to create a PagerDuty integration. There are instructions
`here <https://support.pagerduty.com/docs/services-and-integrations#section-events-api-v2>`_ for
creating a new PagerDuty service & integration.

As noted in the PagerDuty documentation, you'll find an integration key (also referred to as a
"routing key") on the Integrations tab for your new service. This key is used to authorize events
created from the PagerDuty events API.

Once your service/integration is created, you can provision a PagerDuty resource and issue PagerDuty
alerts from within your solids.


.. currentmodule:: dagster_pagerduty

.. autodata:: pagerduty_resource
  :annotation: ResourceDefinition
