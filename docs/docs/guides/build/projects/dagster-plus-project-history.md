---
description: Track and manage project history and rollbacks in Dagster+.
sidebar_position: 500
tags: [dagster-plus-feature]
title: Dagster+ project history and rollbacks
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Dagster+ automatically tracks metadata every time a project is loaded, which you can use to understand when changes have been made, and what those changes were. You can also use this metadata to quickly redeploy an older project version.

## Viewing project history

1. In the Dagster+ UI, navigate to the **Deployment** tab.
2. In the row associated with the project you're interested in, click **View history** in the **Updated** column.

TK - update screenshot
![Screenshot highlighting the "Updated" column for a project](/images/dagster-plus/deployment/code-locations/view-code-location-history.png)

This will bring up a modal showing a history of every time that project has been loaded, and metadata associated with that load. If you have connected Dagster+ to a GitHub or GitLab repository, each row will have a link to the commit that was deployed at that point in time.

If a project has been deployed multiple times with identical metadata, these rows will be collapsed together. You can expand them by deselecting **Collapse similar entries** in the top left corner of the modal.

This metadata will also include information regarding assets that have been **added**, **removed**, or **changed**. In the **Assets** column, you can see the keys of assets in any of these categories.

![Screenshot highlighting the column that displays these keys](/images/dagster-plus/deployment/code-locations/code-location-history-metadata.png)

Currently, changes to **code version**, **tags**, **metadata**, **dependencies** and **partitions definition** are tracked. Clicking on any of these assets brings you to its **Asset details** page. Here, you can find the **Change history** tab, and see detailed information regarding each time the asset definition has changed.

![Screenshot highlighting the Change History tab for an asset](/images/dagster-plus/deployment/code-locations/asset-change-history.png)

## Rolling back to a previous version

:::note

To initiate a rollback, you'll need [**Organization**, **Admin**, or **Editor** permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions).

:::

If you notice an issue with newly deployed code, or your code fails to deploy successfully, you can quickly roll back to a previously deployed image that's known to work properly.

1. In the Dagster+ UI, navigate to the **Deployment** tab.
2. In the row associated with the project you're interested in, click **View history** in the **Updated** column.
3. In the **Actions** column click the dropdown menu to the right of **View metadata**, select **Rollback to this version**.

TK - update screenshot
![Screenshot highlighting the "Updated" column for a project](/images/dagster-plus/deployment/code-locations/rollback-code-location.png)

:::tip

You can [create an alert](/guides/observe/alerts/creating-alerts) to let you know when a project fails to load.

:::
