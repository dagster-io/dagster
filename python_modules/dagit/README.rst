============
Dagster UI
============

Eg in dagster_examples

.. code-block:: sh

  python ../../../dagster-ui/bin/dagster-ui  ui -p 3333

Running dev ui:

.. code-block:: sh
  REACT_APP_GRAPHQL_URI="http://localhost:3333/graphql" yarn start

At ``localhost:3000/graphql``

.. code-block:: graphql

  {
    pipeline(name:"pandas_hello_world") {
      name
      description
      solids {
        name
        description
        inputs {
          name
          description
          dependsOn {
            name
          }
          sources {
            sourceType
            description
            arguments {
              name
              description
              type
              isOptional
            }
          }
          expectations {
            name
            description
          }
        }
        output {
          materializations {
            name
            description
            arguments {
              name
              description
              type
              isOptional
            }
          }
          expectations {
            name
            description
          }
        }
      }
      context {
        name
        description
        arguments {
          name
          description
          type
          isOptional
        }
      }
    }
  }
