External Assets (Experimental)
==============================

Instance API
------------

External asset events can be recorded using :py:func:`DagsterInstance.report_runless_asset_event` on :py:class:`DagsterInstance`.

.. code-block:: python
    from dagster import DagsterInstance, AssetMaterialization, AssetKey

    instance = DagsterInstance.get()
    instance.report_runless_asset_event(AssetMaterialization(AssetKey('my_asset')))

Rest API
--------

The `dagster-webserver` makes available endpoints for reporting asset events.

`/report_asset_materialization/`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A `POST` request made to this endpoint with the required information will result in an `AssetMaterialization` event being recorded. Parameters can be passed in multiple ways, listed in precedence order below.

**Params**
* `asset_key` (required)
  * URL: the asset key can be specified as path components after `/report_asset_materialization/`, where each `/` delimits parts of a multipart :py:class:`AssetKey`.
  * JSON Body `asset_key`: value is passed to the :py:class:`AssetKey` constructor.
  * Query Param `asset_key`: accepts string or json encoded array for multipart keys.
* `metadata` (optional)
  * JSON Body `metadata`: value is passed to the :py:class:`AssetMaterialization` constructor.
  * Query Param `metadata`: accepts json encoded object.
* `data_version` (optional)
  * JSON Body `data_version`: value is passed to the :py:class:`AssetMaterialization` constructor.
  * Query Param `data_version`: value is passed to the :py:class:`AssetMaterialization` constructor.
* `description` (optional)
  * JSON Body `description`: value is passed to the :py:class:`AssetMaterialization` constructor.
  * Query Param `description`: value is passed to the :py:class:`AssetMaterialization` constructor.
* `partition` (optional)
  * JSON Body `partition`: value is passed to the :py:class:`AssetMaterialization` constructor.
  * Query Param `partition`: value is passed to the :py:class:`AssetMaterialization` constructor.
