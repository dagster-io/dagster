External Assets (Experimental)
==============================

Instance API
------------

External asset events can be recorded using :py:func:`DagsterInstance.report_runless_asset_event` on :py:class:`DagsterInstance`.

**Example:** reporting an asset materialization

.. code-block:: python

    from dagster import DagsterInstance, AssetMaterialization, AssetKey

    instance = DagsterInstance.get()
    instance.report_runless_asset_event(AssetMaterialization(AssetKey('raw_orders_asset')))

----

REST API
--------

The ``dagster-webserver`` makes available endpoints for reporting asset events.

/report_asset_materialization/
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``POST`` request made to this endpoint with the required information will result in an `AssetMaterialization` event being recorded.

Parameters can be passed in multiple ways and will be considered in the following order:

1. URL (``asset_key`` only)
2. JSON body (`Content-Type: application/json` header)
3. Query parameter

Refer to the following table for the list of parameters and how each one can be passed to the API.

Returns JSON:
* empty object with status 200 on success
* `{error: ...}` with status 400 on invalid input

**Params**

.. list-table::
   :widths: 15 15 70
   :header-rows: 1

   * - **Name**
     - **Required/Optional**
     - **Description**
   * - asset_key
     - Required
     - **May be passed as URL path components, JSON, or a query parameter**:
       * **URL**: The asset key can be specified as path components after `/report_asset_materialization/`, where each `/` delimits parts of a multipart :py:class:`AssetKey`.

       * **JSON body**: Value is passed to the :py:class:`AssetKey` constructor.

       * **Query parameter**: Accepts string or JSON encoded array for multipart keys.
   * - metadata
     - Optional
     - **May be passed as JSON or a query parameter**:
       * **JSON body**: Value is passed to the :py:class:`AssetMaterialization` constructor.

       * **Query parameter**: Accepts JSON encoded object.
   * - data_version
     - Optional
     - **May be passed in JSON body or as query parameter.** Value is passed to the :py:class:`AssetMaterialization` constructor.
   * - description
     - Optional
     - **May be passed in JSON body or as query parameter.** Value is passed to the :py:class:`AssetMaterialization` constructor.
   * - partition
     - Optional
     - **May be passed in JSON body or as query parameter.** Value is passed to the :py:class:`AssetMaterialization` constructor.

**Example:** report an asset materialization against locally running webserver

.. code-block:: bash

    curl -X POST localhost:3000/report_asset_materialization/raw_orders_asset

**Example:** report an asset materialization against Dagster Cloud with json body via curl (required authentication done via `Content-Type: application/json` header).

.. code-block:: bash

    curl --request POST \
        --url https://example-org.dagster.cloud/example-deployment/report_asset_materialization/ \
        --header 'Content-Type: application/json' \
        --header 'Dagster-Cloud-Api-Token: token' \
        --data '{
            "asset_key": "raw_orders_asset",
            "metadata": {
                "rows": 10
            },
        }'


**Example:** report an asset materialization against an open source deployment (hosted at `DAGSTER_WEBSERVER_HOST`) in python using `requests`.

.. code-block:: python

    import requests

    url = f"{DAGSTER_WEBSERVER_HOST}/report_asset_materialization/raw_orders_asset"
    response = requests.request("POST", url)
    response.raise_for_status()

**Example:** report an asset materialization against Dagster Cloud in python using `requests` (required authentication done via `Content-Type: application/json` header).

.. code-block:: python

    import requests

    url = "https://example-org.dagster.cloud/example-deployment/report_asset_materialization/"

    payload = {
        "asset_key": "raw_orders_asset",
        "metadata": {"rows": 10},
    }
    headers = {
        "Content-Type": "application/json",
        "Dagster-Cloud-Api-Token": "token"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    response.raise_for_status()
