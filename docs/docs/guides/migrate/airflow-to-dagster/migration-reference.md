---
title: 'Airflow to Dagster migration reference'
sidebar_position: 50
---

`dagster-airlift` is a toolkit for observing and migrating Airflow DAGs within Dagster. This reference page provides additional information for working with `dagster-airlift` that is not provided within the migration guides.

- [Supporting custom authorization](#supporting-custom-authorization)
- [Dagster Plus Authorization](#dagster-authorization)
- [Dealing with changing Airflow](#dealing-with-changing-airflow)
- [Automating changes to code locations](#automating-changes-to-code-locations)
- [Peering to multiple Airflow instances](#peering-to-multiple-airflow-instances)
- [Customizing DAG proxying operator](#customizing-dag-proxying-operator)

## Supporting custom authorization

If your Dagster deployment lives behind a custom auth backend, you can customize the Airflow-to-Dagster proxying behavior to authenticate to your backend. `proxying_to_dagster` can take a parameter `dagster_operator_klass`, which allows you to define a custom `BaseProxyTasktoDagsterOperator` class. This allows you to override how a session is created. Let's say for example, your Dagster installation requires an access key to be set whenever a request is made, and that access key is set in an Airflow `Variable` called `my_api_key`. We can create a custom `BaseProxyTasktoDagsterOperator` subclass which will retrieve that variable value and set it on the session, so that any requests to Dagster's graphql API will be made using that api key.

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/custom_operator_examples/custom_proxy.py" />

## Dagster+ authorization

You can use a custom proxy operator to establish a connection to a Dagster plus deployment. The below example proxies to Dagster Plus using organization name, deployment name, and user token set as Airflow Variables. To set a Dagster+ user token, see "[Managing user tokens in Dagster+](/dagster-plus/deployment/management/tokens/user-tokens)".

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/custom_operator_examples/plus_proxy_operator.py" />

## Dealing with changing Airflow

In order to make spin-up more efficient, `dagster-airlift` caches the state of the Airflow instance in the dagster database, so that repeat fetches of the code location don't require additional calls to Airflow's rest API. However, this means that the Dagster definitions can potentially fall out of sync with Airflow. Here are a few different ways this can manifest:

- A new Airflow DAG is added. The lineage information does not show up for this dag, and materializations are not recorded.
- A DAG is removed. The polling sensor begins failing, because there exist assets which expect that DAG to exist.
- The task dependency structure within a DAG changes. This may result in `unsynced` statuses in Dagster, or missing materializations. This is not an exhaustive list of problems, but most of the time the tell is that materializations are missing, or assets are missing. When you find yourself in this state, you can force `dagster-airlift` to reload Airflow state by reloading the code location. To do this, go to the `Deployment` tab on the top nav, and click `Redeploy` on the code location relevant to your asset. After some time, the code location should be reloaded with refreshed state from Airflow.

## Automating changes to code locations

If changes to your Airflow instance are controlled by a CI/CD process, you can use the Dagster GraphQL client to add a step to automatically trigger a redeploy of the relevant code location. To learn more, see the [Dagster GraphQL client docs](/guides/operate/graphql/graphql-client).

## Peering to multiple Airflow instances

Airlift supports peering to multiple Airflow instances, as you can invoke `build_defs_from_airflow_instance` multiple times and combine them with `Definitions.merge`:

```python
from dagster import Definitions

from dagster_airlift.core import AirflowInstance, build_defs_from_airflow_instance

defs = Definitions.merge(
    build_defs_from_airflow_instance(
        airflow_instance=AirflowInstance(
            auth_backend=BasicAuthBackend(
                webserver_url="http://yourcompany.com/instance_one",
                username="admin",
                password="admin",
            ),
            name="airflow_instance_one",
        )
    ),
    build_defs_from_airflow_instance(
        airflow_instance=AirflowInstance(
            auth_backend=BasicAuthBackend(
                webserver_url="http://yourcompany.com/instance_two",
                username="admin",
                password="admin",
            ),
            name="airflow_instance_two",
        )
    ),
)
```

## Customizing DAG proxying operator

Similar to how we can customize the operator we construct on a per-DAG basis, we can customize the operator we construct on a per-DAG basis. We can use the `build_from_dag_fn` argument of `proxying_to_dagster` to provide a custom operator in place of the default.

For example, in the following example we can see that the operator is customized to provide an authorization header which authenticates Dagster.

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/custom_operator_examples/custom_dag_level_proxy.py" />

`BaseProxyDAGToDagsterOperator` has three abstract methods which must be implemented:

- `get_dagster_session`, which controls the creation of a valid session to access the Dagster graphql API.
- `get_dagster_url`, which retrieves the domain at which the dagster webserver lives.
- `build_from_dag`, which controls how the proxying task is constructed from the provided DAG.
