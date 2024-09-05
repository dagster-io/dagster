External assets (Experimental)
==============================

As Dagster doesn't control scheduling or materializing `external assets <https://docs.dagster.io/concepts/assets/external-assets>`_, it's up to you to keep their metadata updated. The APIs in this reference can be used to keep external assets updated in Dagster.

----

Instance API
------------

External asset events can be recorded using :py:func:`DagsterInstance.report_runless_asset_event` on :py:class:`DagsterInstance`.

**Example:** Reporting an asset materialization:

.. code-block:: python

    from dagster import DagsterInstance, AssetMaterialization, AssetKey

    instance = DagsterInstance.get()
    instance.report_runless_asset_event(AssetMaterialization(AssetKey("example_asset")))

**Example:** Reporting an asset check evaluation:

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

Refer to the `External assets REST API reference <https://docs.dagster.io/apidocs/external-assets-rest>`_ for information and examples on the available APIs.