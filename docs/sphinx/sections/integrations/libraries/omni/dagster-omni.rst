Omni (dagster-omni)
-----------------------------------------------------

Dagster allows you to represent your Omni documents as assets, with dependencies on the data
assets (e.g. database tables) that they depend on. This allows you to understand how changes to
upstream data may interact with end product dashboards.

.. currentmodule:: dagster_omni

**************************
OmniComponent
**************************

.. autoclass:: OmniComponent
    :members:

The main class for interacting with Omni is the ``OmniComponent``. This class is responsible for connecting to your Omni instance,
fetching information about your documents, and building Dagster asset definitions from that information.

``OmniComponent`` is a ``StateBackedComponent``, which means that it only fetches updated information from the Omni API when you tell 
it to, and you will need to redeploy your code location after updating your metadata in order to see those changes.

The simplest way to update the stored state of your ``OmniComponent`` is to use the ``dg utils refresh-component-state`` command. When
deploying your code location, this command should be executed in your CI/CD workflow (e.g. github actions).

.. TODO add link to state-backed component docs once they exist