---
title: "Code location history and rollbacks"
displayed_sidebar: "dagsterPlus"
sidebar_position: 4
sidebar_label: "Code location history and rollbacks"
---

# Code location history and rollbacks

Dagster+ automatically tracks metadata every time a code location is loaded. This can be used to understand when changes have been made, and what those changes were. In addition, this metadata can be used to quickly redeploy an older version.

<details>
  <summary>Prerequisites</summary>

Before continuing, you should be familiar with:

- [Code Locations](/dagster-plus/deployment/code-locations)

</details>

## Viewing code location history

1. In the Dagster+ UI, navigate to the **Deployment** tab.
2. In the row associated with the code location you're interested in, click **View history** in the **Updated** column.

![Screenshot highlighting the "Updated" column for a code location](/img/placeholder.svg)

This will bring up a modal showing a history of every time that code location has been loaded, and metadata associated with that load. If you have connected Dagster+ to a GitHub or GitLab repository, each row will have a link to the commit that was deployed at that point in time.

If a code location has been deployed multiple times with identical metadata, these rows will be collapsed together. You can expand them by deselecting **Collapse similar entries** in the top left corner of the modal.

This metadata will also include information regarding assets that have been **added**, **removed**, or **changed**. In the **Assets** column, you can see the keys of assets in any of these categories.

![Screenshot highlighting the column that displays these keys](/img/placeholder.svg)

Currently, changes to **code version**, **tags**, **metadata**, **dependencies** and **partitions definition** are tracked. Clicking on any of these assets brings you to its **Asset details** page. Here, you can find the **Change history** tab, and see detailed information regarding each time the asset definition has changed.

![Screenshot highlighting the Change History tab for an asset](/img/placeholder.svg)

## Rolling back to a previous code location version

:::note
To initiate a rollback, you'll need **Organization**, **Admin**, or **Editor** permissions
:::

If you notice an issue with newly deployed code, or your code fails to deploy successfully, you can quickly roll back to a previously deployed image that's known to work properly.

1. In the Dagster+ UI, navigate to the **Deployment** tab.
2. In the row associated with the code location you're interested in, click **View history** in the **Updated** column.
3. In the **Actions** column click the dropdown menu to the right of **View metadata**, select **Rollback to this version**.

![Screenshot highlighting the "Updated" column for a code location](/img/placeholder.svg)

## Next steps

- Learn more about [Code Locations](/dagster-plus/deployment/code-locations)
- Learn how to [Alert when a code location fails to load](/dagster-plus/deployment/alerts#alerting-when-a-code-location-fails-to-load)
