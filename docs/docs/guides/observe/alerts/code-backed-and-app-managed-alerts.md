---
description: Alert policies defined in YAML and alert policies created in the Dagster+ UI coexist. Learn how to tell them apart, what a sync changes, and how to move an alert between the two.
sidebar_position: 250
tags: [dagster-plus-feature]
title: Code-backed and app-managed alerts
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Alert policies can be created in the Dagster+ UI or synced from a YAML file. Both can exist in the same deployment at the same time, so one team can keep its alerts in version control while another manages theirs in the UI. For more information on both approaches, see [Creating alert policies](/guides/observe/alerts/creating-alerts).

Every alert policy has a source:

- **Code-backed** — the alert policy configuration is maintained in a YAML file, and synced using the `dg` or `dagster-cloud` CLI.
- **App-managed** — the alert policy configuration is maintained in the Dagster+ UI.

The alerts list labels each policy with its source. Policies that have not been updated since this feature was introduced are unlabeled until their next update.

## What a sync changes

A sync applies every alert policy in the YAML file, and deletes code-backed policies that the file no longer contains. It leaves everything else alone:

| Policy      | Not in the synced file |
| ----------- | ---------------------- |
| Code-backed | Deleted                |
| App-managed | Kept                   |
| Unlabeled   | Kept                   |

Dagster+ records that a policy came from a sync, but not which file it came from, so keep all of your code-backed alert policies in the file you sync. Syncing a second file would delete the policies defined in the first.

:::note

Before August 2026, a sync replaced **all** alert policies in the deployment, which deleted any alert policy created in the UI the next time a sync ran. Dagster+ applies the current behavior server-side, so you do not need to update your CLI to get it.

:::

## Move an app-managed alert policy into code

1. On the alerts page, open the menu next to **Create alert policy** and select **Export policies**, then **Download as YAML**. The downloaded `alerts.yaml` contains every alert policy in the deployment.
2. Copy the alert policy you want into the YAML file you sync, keeping its existing name.
3. Sync the file.

Keeping the same name marks the existing alert policy as code-backed rather than creating a new one. The existing alert policy keeps its history, and its notifications are uninterrupted.

If the config in your YAML file differs from the config set in the UI, the code version becomes the source of truth. Dagster+ shows a warning on that alert policy with the configuration it replaced, so you can fold in anything you meant to keep. Dismiss the warning once you've reconciled the alert policy config.

## Move a code-backed alert policy into the UI

1. Copy the alert policy out of your YAML file.
2. Remove it from the file and sync. The sync deletes the alert policy.
3. Recreate it in the UI, either with **Create alert policy** or by pasting the config into the YAML editor under **Edit policies**.

The alert policy will not fire between the sync that deleted it and when you recreate it in the UI.

## Working with a code-backed alert policy in the UI

Your YAML file is the source of truth for a code-backed alert policy. The UI disables changes that the next sync would override:

| Action                   | Code-backed alert policy           |
| ------------------------ | ---------------------------------- |
| Mute                     | Allowed                            |
| Send sample notification | Allowed                            |
| Edit configuration       | Edit the YAML file and sync        |
| Delete                   | Remove from the YAML file and sync |
| Enable or disable        | Edit the YAML file and sync        |

## Default alert policies

New organizations start with two alert policies, `[Dagster Plus] Credit Limit Exceeded` and `[Dagster Plus] Run Exceeds 24 Hours`. These alert policies are app-managed.
