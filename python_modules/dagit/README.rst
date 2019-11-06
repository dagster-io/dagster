============
Dagster UI
============

Usage
~~~~~
Eg in dagster_examples

.. code-block:: sh

  dagit -p 3333

Running dev ui:

.. code-block:: sh
  REACT_APP_GRAPHQL_URI="ws://localhost:3333/graphql" yarn start

Updating mock GraphQL requests / responses used in tests:

.. code-block:: sh

  yarn run download-mocks

