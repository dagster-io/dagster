---
title: "Asset observations"
description: Dagster provides functionality to record metadata about assets.
sidebar_position: 5000
---

An asset observation is an event that records metadata about a given asset. Unlike asset materializations, asset observations do not signify that an asset has been mutated.

## Relevant APIs

| Name                                   | Description                                                          |
| -------------------------------------- | -------------------------------------------------------------------- |
| <PyObject section="assets" module="dagster" object="AssetObservation" /> | Dagster event indicating that an asset's metadata has been recorded. |
| <PyObject section="assets" module="dagster" object="AssetKey" />         | A unique identifier for a particular external asset.                 |

## Overview

<PyObject section="assets" module="dagster" object="AssetObservation" /> events are used to record metadata in Dagster
about a given asset. Asset observation events can be logged at runtime within ops and assets. An asset must be defined using the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator or have existing materializations in order for its observations to be displayed.

## Logging an AssetObservation from an op

To make Dagster aware that we have recorded metadata about an asset, we can log an <PyObject section="assets" module="dagster" object="AssetObservation" /> event from within an op. To do this, we use the method <PyObject section="execution" module="dagster" object="OpExecutionContext.log_event" /> on the context:

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/observations.py" startAfter="start_observation_asset_marker_0" endBefore="end_observation_asset_marker_0" />

We should now see an observation event in the event log when we execute this asset.

![asset observation](/images/guides/build/assets/asset-observations/observation.png)

### Attaching Metadata to an AssetObservation

There are a variety of types of metadata that can be associated with an observation event, all through the <PyObject section="metadata" module="dagster" object="MetadataValue" /> class. Each observation event optionally takes a dictionary of metadata that is then displayed in the event log and the **Asset Details** page. Check our API docs for <PyObject section="metadata" module="dagster" object="MetadataValue" /> for more details on the types of event metadata available.

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/observations.py" startAfter="start_observation_asset_marker_2" endBefore="end_observation_asset_marker_2" />

In the **Asset Details** page, we can see observations in the Asset Activity table:

![asset activity observation](/images/guides/build/assets/asset-observations/asset-activity-observation.png)

### Specifying a partition for an AssetObservation

If you are observing a single slice of an asset (e.g. a single day's worth of data on a larger table), rather than mutating or creating it entirely, you can indicate this to Dagster by including the `partition` argument on the object.

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/observations.py" startAfter="start_partitioned_asset_observation" endBefore="end_partitioned_asset_observation" />

### Observable source assets

<PyObject section="assets" module="dagster" object="SourceAsset" /> objects may have a user-defined observation function
that returns a `DataVersion`. Whenever the observation
function is run, an <PyObject section="assets" module="dagster" object="AssetObservation" /> will be generated for
the source asset and tagged with the returned data version. When an asset is
observed to have a newer data version than the data version it had when a
downstream asset was materialized, then the downstream asset will be given a
label in the Dagster UI that indicates that upstream data has changed.

<PyObject section="assets" module="dagster" object="AutomationCondition" pluralize /> can be used to automatically
materialize downstream assets when this occurs.

The <PyObject section="assets" module="dagster" object="observable_source_asset" /> decorator provides a convenient way to define source assets with observation functions. The below observable source asset takes a file hash and returns it as the data version. Every time you run the observation function, a new observation will be generated with this hash set as its data version.

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/observable_source_assets.py" startAfter="start_plain" endBefore="end_plain" />

When the file content changes, the hash and therefore the data version will change - this will notify Dagster that downstream assets derived from an older value (i.e. a different data version) of this source asset might need to be updated.

Source asset observations can be triggered via the "Observe sources" button in the UI graph explorer view. Note that this button will only be visible if at least one source asset in the current graph defines an observation function.

![observable source asset](/images/guides/build/assets/asset-observations/observe-sources.png)

Source asset observations can also be run as part of an asset job. This allows you to run source asset observations on a schedule:

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/observable_source_assets.py" startAfter="start_schedule" endBefore="end_schedule" />

:::note

Currently, source asset observations cannot be run as part of a standard asset job that materializes assets. The `selection` argument to <PyObject section="assets" module="dagster" object="define_asset_job" /> must target only observable source assets-- an error will be thrown if a mix of regular assets and observable source assets is selected.

:::
