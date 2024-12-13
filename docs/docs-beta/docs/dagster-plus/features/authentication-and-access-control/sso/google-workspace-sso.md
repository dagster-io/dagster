---
title: Setting up Google Workspace SSO for Dagster+
sidebar_label: 'Google Workspace SSO'
sidebar_position: 300
---

In this guide, you'll configure Google Workspace to use single sign-on (SSO) with your Dagster+ organization.

<details>
  <summary>Prerequisites</summary>

To complete the steps in this guide, you'll need:

- **The following in Google**:
  - An existing Google account
  - [Workspace Admin permissions](https://support.google.com/a/answer/6365252?hl=en&ref_topic=4388346)
- **To install the [`dagster-cloud` CLI](/todo)**
- **The following in Dagster+:**
  - A Pro plan
  - [Access to a user token](/todo)
  - [Organization Admin permissions](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions) in your organization

</details>

## Step 1: Add the Dagster+ app in Google Workspace \{#dagster-app}

1. Navigate to your [Google Admin Console](https://admin.google.com).
2. Using the sidebar, navigate to **Apps > Web and mobile apps**:

   ![Google Workspace Sidebar](/img/placeholder.svg)

3. On the **Web and mobile apps** page, click **Add App > Add custom SAML app**:
   ![Add App](/img/placeholder.svg)
   This opens a new page for adding app details.

## Step 2: Configure SSO in Google Workspace \{#configure-sso}

1. On the **App details** page:

   1. Fill in the **App name** field.
   2. Fill in the **Description** field.

      The page should look similar to the following:

      ![Application Details](/img/placeholder.svg)

   3. Click **Continue**.

2. On the **Google Identity Provider details** page, click **Continue**. No action is required for this page.
3. On the **Service provider details** page:

   1. In the **ACS URL** and **Entity ID** fields:

      Copy and paste the following URL, replacing `<organization_name>` with your Dagster+ organization name:

      ```
      https://<organization_name>.dagster.cloud/auth/saml/consume
      ```

   2. Check the **Signed Response** box. The page should look similar to the image below. In this example, the organization's name is `hooli` and the Dagster+ domain is `https://hooli.dagster.cloud`:

      ![Service Provider Details](/img/placeholder.svg)

   3. When finished, click **Continue**.

4. On the **Attributes** page:

   1. Click **Add mapping** to add and configure the following attributes:

      - **Basic Information > First Name** - `FirstName`
      - **Basic Information > Last Name** - `LastName`
      - **Basic Information > Email** - `Email`

      The page should look like the following image:

      ![Attribute Mapping](/img/placeholder.svg)

   2. Click **Finish**.

## Step 3: Upload the SAML metadata to Dagster+ \{#upload-saml}

Next, you'll save and upload the application's SAML metadata to Dagster+. This will enable single sign-on.

1. In your Google Workspace, open the Dagster+ application you added in [Step 2](#configure-sso).
2. Click **Download metadata**:

   ![SAML Metadata](/img/placeholder.svg)

3. In the modal that displays, click **Download metadata** to start the download. Save the file to your computer.
4. After you've downloaded the SAML metadata file, upload it to Dagster+ using the `dagster-cloud` CLI:

   ```shell
   dagster-cloud organization settings saml upload-identity-provider-metadata <the_path/to/metadata> \
      --api-token=<user_token> \
      --url https://<your_organization_name>.dagster.cloud
   ```

## Step 4: Grant access to users \{#grant-access}

In this step, you'll assign users in your Google Workspace to the Dagster+ application. This allows members of the workspace to log in to Dagster+ using their credentials when the single sign-on flow is initiated.

1. In the Google Workspace Dagster+ application, click **User access**.
2. Select an organizational unit.
3. Click **ON for everyone**.
4. Click **Save**.

   ![Assign New Login](/img/placeholder.svg)

import TestSSO from '../../../../partials/\_TestSSO.md';

<TestSSO />

In the Google Workspace portal, click the **Dagster+ icon**. If successful, you'll be automatically signed into your Dagster+ organization.
