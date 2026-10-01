---
title: 'Managing components in the Dagster+ UI'
description: Add, edit, and delete component instances directly from the Dagster+ UI, without editing code.
sidebar_position: 600
tags: [dagster-plus-feature]
---

import Preview from '@site/docs/partials/_Preview.md';

<Preview />

In Dagster+, you can add, edit, and delete component instances for a code location directly from the UI. This lets you manage components without editing files in your project, and is useful for iterating on component configuration or for teams that prefer a UI-driven workflow.

Components created this way are **app-managed:** their configuration is stored by Dagster+ and applied to the code location, rather than living in your project's source files. Components defined in code (**code-backed**) continue to appear alongside them and are read-only in the UI.

## Prerequisites

To manage components in the UI, you need:

- A Dagster+ deployment.
- At least one component type that supports UI creation installed in the code location.
- The **Enable experimental component instance UI** feature flag turned on. This feature is off by default, and the flag applies per user account, so each person enables it for themselves:
  1. Open **User settings** from the account menu.
  2. Under **Feature flags**, enable **Enable experimental component instance UI**.

## Open the Components tab

1. Navigate to the code location you want to manage.
2. Open the **Components** tab.

The Components tab has two sub-tabs:

- **Library:** the component types available in the code location.
- **Instances:** the component instances configured in the code location. This is where app-managed components are listed and managed.

The Instances table shows each component's name, source, and state. App-managed components are labeled **App-managed**; components defined in code are labeled **Code-backed** and can be viewed but not edited from the UI.

## Add a component

1. On the **Instances** sub-tab, select **Add**.
2. Choose a component type from the list. You can search by name. Only component types that support UI creation appear here.
3. Fill in the component's configuration in the YAML editor. The **Add component** button stays disabled until the configuration is valid YAML.
4. Select **Add component**.

Dagster+ saves the component and reloads the code location so the new component takes effect.

## Edit, view, or delete a component

Each app-managed component has an overflow menu (**⋯**) with **Edit**, **View config**, and **Delete** actions. Deleting a component removes it from the code location and cannot be undone.

## When a change is invalid

If a change puts the code location into a failed state — for example, because the configuration doesn't match the component type — the UI shows the error and offers to revert the change, restoring the previous configuration (or removing the component you just added) so the location doesn't stay broken.

:::note

Changes made in the UI apply to the deployment you are working in. Managing components from the UI is separate from defining components in code; a component managed in the UI is not written back to your project's source files.

:::
