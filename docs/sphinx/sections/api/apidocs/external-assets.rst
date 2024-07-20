External assets (Experimental)
==============================

As Dagster doesn't control scheduling or materializing `external assets </concepts/assets/external-assets>`_, you need to keep their metadata updated. Use the APIs in this reference to keep external assets updated in Dagster.

----

Instance API
------------

You can record external asset events using :py:func:`DagsterInstance.report_runless_asset_event` on :py:class:`DagsterInstance`.

**Example:** reporting an asset materialization:

.. code-block:: python

    from dagster import DagsterInstance, AssetMaterialization, AssetKey

    instance = DagsterInstance.get()
    instance.report_runless_asset_event(AssetMaterialization(AssetKey("example_asset")))

**Example:** reporting an asset check evaluation:

.. code-block:: python

    from dagster import DagsterInstance, AssetCheckEvaluation, AssetCheckKey

    instance = DagsterInstance.get()
    instance.report_runless_asset_event(
      AssetCheckEvaluation(
        asset_key=AssetKey("example_asset"),
        check_name="example_check",
        passed=True
      )
    )

----

REST API
--------

Refer to the `External assets REST API reference </apidocs/external-assets-rest>`_ for information and examples on the available APIs.