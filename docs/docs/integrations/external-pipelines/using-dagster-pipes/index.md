---
title: 'Using Dagster pipes'
description: 'Learn how to use the built-in subprocess implementation of Dagster Pipes to invoke a subprocess with a given command and environment'
sidebar_position: 10
canonicalUrl: '/integrations/external-pipelines/using-dagster-pipes'
slug: '/integrations/external-pipelines/using-dagster-pipes'
---

In this guide, we’ll show you how to use [Dagster Pipes](/integrations/external-pipelines) with Dagster’s built-in subprocess <PyObject section="pipes" module="dagster" object="PipesSubprocessClient" /> to run a local subprocess with a given command and environment. You can then send information such as structured metadata and logging back to Dagster from the subprocess, where it will be visible in the Dagster UI.

To get there, you'll:

- [Create a Dagster asset that invokes a subprocess](/integrations/external-pipelines/using-dagster-pipes/create-subprocess-asset)
- [Modify existing code to work with Dagster Pipes to send information back to Dagster](/integrations/external-pipelines/using-dagster-pipes/modify-external-code)
- Learn about using Dagster Pipes with other entities in the Dagster system in the [Reference](/integrations/external-pipelines/using-dagster-pipes/reference) section

:::note

This guide focuses on using an out-of-the-box <PyObject section="pipes" module="dagster" object="PipesSubprocessClient" /> resource. For further customization with the subprocess invocation, use <PyObject section="libraries" integration="pipes" module="dagster_pipes" object="open_dagster_pipes"/> approach instead. Refer to [Customizing Dagster Pipes protocols](/integrations/external-pipelines/dagster-pipes-details-and-customization) for more info.

:::

## Ready to get started?

You can get started by [creating a Dagster asset that executes a subprocess](/integrations/external-pipelines/using-dagster-pipes/create-subprocess-asset).
