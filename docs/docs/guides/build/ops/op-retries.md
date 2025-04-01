---
title: 'Op retries'
description: Retry ops on exception using RetryPolicy and RetryRequested
sidebar_position: 300
---

import OpsNote from '@site/docs/partials/\_OpsNote.md';

<OpsNote />

When an exception occurs during op execution, Dagster provides tools to retry that op within the same job run.

## Relevant APIs

| Name                                                  | Description                                                                   |
| ----------------------------------------------------- | ----------------------------------------------------------------------------- |
| <PyObject section="ops" module="dagster" object="RetryRequested" /> | An exception that can be thrown from the body of an op to request a retry     |
| <PyObject section="ops" module="dagster" object="RetryPolicy"  />   | A declarative policy to attach which will have retries requested on exception |
| <PyObject section="ops" module="dagster" object="Backoff"  />       | Modification to delay between retries based on attempt number                 |
| <PyObject section="ops" module="dagster" object="Jitter"  />        | Random modification to delay beween retries                                   |

## Overview

In Dagster, code is executed within an [op](/guides/build/ops/). Sometimes this code can fail for transient reasons, and the desired behavior is to retry and run the function again.

Dagster provides both declarative <PyObject section="ops" module="dagster" object="RetryPolicy"  />s as well as manual <PyObject section="ops" module="dagster" object="RetryRequested" /> exceptions to enable this behavior.

## Using op retries

Here we start off with an op that is causing us to have to retry the whole job anytime it fails.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/retries.py" startAfter="problem_start" endBefore="problem_end" />

### `RetryPolicy`

To get this op to retry when an exception occurs, we can attach a <PyObject section="ops" module="dagster" object="RetryPolicy" />.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/retries.py" startAfter="policy_start" endBefore="policy_end" />

This improves the situation, but we may need additional configuration to control how many times to retry and/or how long to wait between each retry.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/retries.py" startAfter="policy2_start" endBefore="policy2_end" />

In addition to being able to set the policy directly on the op definition, it can also be set on specific invocations of an op, or a <PyObject section="jobs" module="dagster" object="job" decorator /> to apply to all ops contained within.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/retries.py" startAfter="policy3_start" endBefore="policy3_end" />

### `RetryRequested`

In certain more nuanced situations, we may need to evaluate code to determine if we want to retry or not. For this we can use a manual <PyObject section="ops" module="dagster" object="RetryRequested" /> exception.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/retries.py" startAfter="manual_start" endBefore="manual_end" />

Using `raise from` will ensure the original exceptions information is captured by Dagster.
