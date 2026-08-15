---
title: 'Refreshing state in the Dagster+ UI'
description: Refresh a state-backed component's state from the Dagster+ UI without redeploying your code.
sidebar_position: 400
tags: [dagster-plus-feature]
---

import Preview from '@site/docs/partials/_Preview.md';

<Preview />

A state-backed component that uses the [`VERSIONED_STATE_STORAGE`](/guides/build/components/state-backed-components#versioned-state-storage) strategy stores its state in a state storage backend and loads it at runtime. In Dagster+, you can refresh that state directly from the UI so the code location picks up the latest state without a full redeploy.

This is useful when the external system a component reflects has changed — for example, when models, tables, or reports have been added upstream — and you want the component's definitions to catch up without waiting for your next deployment. For refreshing state as part of a deployment or in an automated pipeline, see [Managing state in CI/CD](/guides/build/components/state-backed-components/managing-state-in-ci-cd).

## Prerequisites

- A Dagster+ deployment.
- The **Enable experimental component instance UI** feature flag turned on, from **User settings → Feature flags → Enable experimental component instance UI**. The **Refresh** action is part of the component management UI, which is a preview feature.
- A component that uses the `VERSIONED_STATE_STORAGE` state management strategy. See [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

## Refresh a component's state

1. Navigate to the code location and open the **Components** tab.
2. On the **Instances** sub-tab, find the component in the table.
3. In the **State** column, select **Refresh**.

The **State** column shows how recently each component's state was refreshed. The **Refresh** action is available only for components that use `VERSIONED_STATE_STORAGE`; components whose state is fixed at deploy time don't show a Refresh action — update those by redeploying.

## What happens during a refresh

When you refresh, Dagster+ fetches the component's latest state from the source system. The refresh resolves in one of three ways:

- **Completed:** the new state is fetched within a few seconds and the UI shows **Refreshed component state.**
- **Still running:** if it takes longer, the UI shows **Refreshing…** and keeps checking for up to five minutes. If it hasn't finished by then, the UI tells you it didn't complete and to check the logs.
- **Failed:** if the refresh fails — for example, because the source system is unavailable — the UI shows the error message.

Refreshing updates only the component's state; it doesn't deploy new code.
