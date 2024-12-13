---
title: Setting up Okta SSO for Dagster+
sidebar_label: 'Okta SSO'
sidebar_position: 400
---

In this guide, you'll configure Okta to use single sign-on (SSO) with your Dagster+ organization.

<details>
  <summary>Prerequisites</summary>

To complete the steps in this guide, you'll need:

- **An existing Okta account**
- **To install the [`dagster-cloud` CLI](/todo)**
- **The following in Dagster+:**
  - A Pro plan
  - [Access to a user token](/todo)
  - [Organization Admin permissions](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions) in your organization

</details>

## Step 1: Add the Dagster+ app in Okta \{#dagster-app}

1. Sign in to your Okta Admin Dashboard.
2. Using the sidebar, click **Applications > Applications**.
3. On the **Applications** page, click **Browse App Catalog**.
4. On the **Browse App Integration Catalog** page, search for `Dagster Cloud`.
5. Add and save the application.

## Step 2: Configure SSO in Okta \{#configure-sso}

1. In Okta, open the Dagster Cloud application and navigate to its **Sign On Settings**.
2. Scroll down to the **Advanced Sign-on settings** section.
3. In the **Organization** field, enter your Dagster+ organization name. This is used to route the SAML response to the correct Dagster+ subdomain.

For example, your organization name is `hooli` and your Dagster+ domain is `https://hooli.dagster.cloud`. To configure this correctly, you'd enter `hooli` into the **Organization** field:

![Okta Subdomain Configuration](/img/placeholder.svg)

4. When finished, click **Done**.

## Step 3: Upload the SAML metadata to Dagster+ \{#upload-saml}

Next, you'll save and upload the application's SAML metadata to Dagster+. This will enable single sign-on.

1. In the **Sign On Settings**, navigate to the **SAML Signing Certificates** section.
2. Click the **Actions** button of the **Active** certificate.
3. Click **View IdP metadata**:

   ![Okta IdP metadata options](/img/placeholder.svg)

   This will open a new page in your browser with the IdP metadata in XML format.

4. Right-click the page and use **Save As** or **Save Page As**:

   ![Save IdP metadata as XML](/img/placeholder.svg)

   In Chrome and Edge, the file will be downloaded as an XML file. In Firefox, choose **Save Page As > Save as type**, then select **All files**.

   :::note
   Copying and pasting the metadata can cause formatting issues that will prevent successful setup. Saving the page directly from the browser will avoid this.
   :::

5. After you've downloaded the metadata file, upload it to Dagster+ using the `dagster-cloud` CLI:

   ```shell
   dagster-cloud organization settings saml upload-identity-provider-metadata <path/to/metadata> \
      --api-token=<user_token> \
      --url https://<organization_name>.dagster.cloud
   ```

## Step 4: Grant access to users \{#grant-access}

Next, you'll assign users to the Dagster+ application in Okta. This will allow them to log in using their Okta credentials when the single sign-on flow is initiated.

1. In the Dagster+ application, navigate to **Assignments**.
2. Click **Assign > Assign to People**.
3. For each user you want to have access to Dagster+, click **Assign** then **Save and Go Back**.

import TestSSO from '../../../../partials/\_TestSSO.md';

<TestSSO />

In the Okta **Applications** page, click the **Dagster+** icon:

![Okta idP Login](/img/placeholder.svg)

If successful, you'll be automatically signed into your Dagster+ organization.
