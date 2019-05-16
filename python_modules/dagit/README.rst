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

Updating api mocks:

.. codeblock:: sh

  REACT_APP_RENDER_API_RESULTS=true REACT_APP_GRAPHQL_URI="ws://localhost:3333/graphql" yarn start

Copy the mocks to `__tests__/mockData.tsx`
