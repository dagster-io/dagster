---
title: 'Op events and exceptions'
description: Within the body of an op, it is possible to communicate with the Dagster framework either by yielding an event, or raising an exception.
sidebar_position: 100
---

import OpsNote from '@site/docs/partials/\_OpsNote.md';

<OpsNote />

Within the body of an op, it is possible to communicate with the Dagster framework either by yielding an event, logging an event, or raising an exception. This page describes these different possibilities and the scenarios in which you might use them.

## Relevant APIs

| Name                                       | Description                                                   |
| ------------------------------------------ | ------------------------------------------------------------- |
| <PyObject section="ops" module="dagster" object="Output"  />              | Dagster event used to yield an output from an op              |
| <PyObject section="ops" module="dagster" object="AssetMaterialization" /> | Dagster event indicating that an op has materialized an asset |
| <PyObject section="assets" module="dagster" object="AssetObservation" />     | Dagster event indicating that an op has observed an asset     |
| <PyObject section="ops" module="dagster" object="ExpectationResult" />    | Dagster event representing the result of a data quality check |
| <PyObject section="ops" module="dagster" object="Failure"  />             | Dagster exception indicating that a failure has occurred      |
| <PyObject section="ops" module="dagster" object="RetryRequested"  />      | Dagster exception requesting the step to be retried           |

## Overview

Within the body of an op, a stream of structured events can be yielded or logged. These events will be processed by Dagster and recorded in the event log, along with some additional context about the op that emitted it.

It is also possible to raise Dagster-specific exceptions, which will indicate to the framework to halt the op execution entirely and perform some action.

### Event metadata

Often, it may be useful to attach some arbitrary information to an event or exception that is not captured by its basic parameters. Through the <PyObject section="metadata" module="dagster" object="MetadataValue"/> class, we provide a consistent interface for specifying this metadata. The available value types are accessible through a static API defined on `MetadataValue`. These include simple datatypes (`MetadataValue.float`, `MetadataValue.int`, `MetadataValue.text`), as well as more complex types such as markdown and json (`MetadataValue.md`, `MetadataValue.json`). Depending on the type of its `value`, metadata will be rendered in the UI in a more useful format than a simple unstructured string.

Metadata is attached to events at construction time, using the `metadata` argument, which takes a dictionary mapping string `labels` to primitive types or `MetadataValue` objects.

## Events

Yielding events from within the body of an op is a useful way of communicating with the Dagster framework. The most critical event to the functionality of Dagster is the <PyObject section="ops" module="dagster" object="Output"/> event, which allows output data to be passed on from one op to the next. However, we also provide interfaces to inform Dagster about external assets and data quality checks during the run of an op.

### Output objects

Because returning a value from an op is such a fundamental part of creating a data pipeline, we have a few different interfaces for this functionality.

For many use cases, Dagster ops can be used directly with python's native type annotations without additional modification.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_output_op_marker" endBefore="end_output_op_marker" />

Check out the docs on [Op Outputs](/guides/build/ops#outputs) to learn more about this functionality.

Dagster also provides the <PyObject section="ops" module="dagster" object="Output"/> object, which opens up additional functionality to outputs when using Dagster, such as [specifying output metadata](#attaching-metadata-to-outputs-experimental) and [conditional branching](/guides/build/ops/graphs#with-conditional-branching), all while maintaining coherent type annotations.

<PyObject section="ops" module="dagster" object="Output"/> objects can be either returned or yielded. The Output
type is also generic, for use with return annotations:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_events.py" startAfter="start_op_output_4" endBefore="end_op_output_4" />

When <PyObject section="ops" module="dagster" object="Output"/> objects are yielded, type annotations cannot be used. Instead, type information can be specified using the `out` argument of the op decorator.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_events.py" startAfter="start_yield_outputs" endBefore="end_yield_outputs" />

#### Attaching metadata to outputs (Experimental)

If there is information specific to an op output that you would like to log, you can use an <PyObject section="ops" module="dagster" object="Output"/> object to attach metadata to the op's output. To do this, use the `metadata` parameter on the object, which expects a mapping of string labels to metadata values.

The `EventMetadata` class contains a set of static wrappers to customize the display of certain types of structured metadata.

The following example demonstrates how you might use this functionality:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_events.py" startAfter="start_op_output_3" endBefore="end_op_output_3" />

### Asset materializations

<PyObject section="ops" module="dagster" object="AssetMaterialization" /> events tell Dagster that you have written some data asset to an external system. The classic example would be writing to a table in a database, but really any sort of persisted object that you would want to keep track of can be considered an asset.

Generally, you'd want to send this event directly after you persist the asset to your external system. All <PyObject section="ops" module="dagster" object="AssetMaterialization" /> events must define an `asset_key`, which is a unique identifier to describe the asset you are persisting. They can optionally include a `partition` if they're persisting a particular [partition](/guides/build/partitions-and-backfills/partitioning-assets) of an asset.

If you're using [asset definitions](/guides/build/assets/), you don't need to record these events explicitly – the framework handles it for you.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_events.py" startAfter="start_asset_op" endBefore="end_asset_op" />

Asset materializations can also be yielded:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_events.py" startAfter="start_asset_op_yield" endBefore="end_asset_op_yield" />

When yielding asset materializations, outputs must also be yielded via an <PyObject section="ops" module="dagster" object="Output"/>.

To learn more about assets and how they are surfaced once you send this event, check out the [Asset Catalog](/guides/operate/webserver#assets) documentation.

#### Attaching metadata to asset materializations

Attaching metadata to Asset Materializations is an important way of tracking aspects of a given asset over time. This functions essentially identically to other events which accept a `metadata` parameter, allowing you to attach a set of structured labels and values to display.

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/materialization_ops.py" startAfter="start_materialization_ops_marker_2" endBefore="end_materialization_ops_marker_2" />

### Asset observations

<PyObject section="assets" module="dagster" object="AssetObservation" /> events record metadata about assets. Unlike
asset materializations, asset observations do not signify that an asset has been
mutated.

Within ops and assets, you can log or yield <PyObject section="assets" module="dagster" object="AssetObservation" /> events at runtime. Similar to attaching metadata to asset materializations, asset observations accept a `metadata` parameter, allowing you to track specific properties of an asset over time.

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/observations.py" startAfter="start_observation_asset_marker_0" endBefore="end_observation_asset_marker_0" />

In the example above, an observation tracks the number of rows in an asset persisted to storage. This information can then be viewed on the [Asset Details](/guides/operate/webserver#assets) page.

To learn more about asset observations, check out the [Asset Observation](/guides/build/assets/metadata-and-tags/asset-observations) documentation.

### Expectation results

Ops can emit structured events to represent the results of a data quality test. The data quality event class is the <PyObject section="ops" module="dagster" object="ExpectationResult" />. To generate an expectation result, we can log or yield an <PyObject section="ops" module="dagster" object="ExpectationResult" /> event in our op.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_events.py" startAfter="start_expectation_op" endBefore="end_expectation_op" />

#### Attaching metadata to expectation results

Like many other event types in Dagster, there are a variety of types of metadata that can be associated with an expectation result event, all through the <PyObject section="metadata" module="dagster" object="MetadataValue"/> class. Each expectation event optionally takes a dictionary of metadata that is then displayed in the event log.

This example shows metadata entries of different types attached to the same expectation result:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_events.py" startAfter="start_metadata_expectation_op" endBefore="end_metadata_expectation_op" />

## Exceptions

Dagster also provides some op-specific exception classes, which can be raised to halt the execution of a op. The behavior after an exception is raised depends on the exception that you use. The exceptions are documented below.

### Failures

A <PyObject section="ops" module="dagster" object="Failure" /> is a kind of [Exception](https://docs.python.org/3/tutorial/errors.html#exceptions) that contains metadata that can be interpreted by the Dagster framework. Like any Exception raised inside an op, it indicates that the op has failed in an unrecoverable way, and that execution should stop.

A <PyObject section="ops" module="dagster" object="Failure" /> can include a dictionary with structured <PyObject section="metadata" module="dagster" object="MetadataValue"/> values, which will be rendered in the UI according to their type. It also has an `allow_retries` argument that can be used to bypass the op's retry policy.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_events.py" startAfter="start_failure_op" endBefore="end_failure_op" />

### Retry requests

<PyObject section="ops" module="dagster" object="RetryRequested" /> exceptions are useful when you experience failures
that are possible to recover from. For example, if you have a flaky operation that
you expect to throw an exception once in a while, you can catch the exception and
throw a <PyObject section="ops" module="dagster" object="RetryRequested" /> to make Dagster halt and re-start op
execution.

You can configure the number of retries to be attempted with the `max_retries` parameter.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_events.py" startAfter="start_retry_op" endBefore="end_retry_op" />
