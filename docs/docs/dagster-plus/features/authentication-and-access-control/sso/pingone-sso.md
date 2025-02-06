---
title: Setting up PingOne SSO for Dagster+
sidebar_label: 'PingOne SSO'
sidebar_position: 600
---

In this guide, you'll configure PingOne to use single sign-on (SSO) with your Dagster+ organization.

<details>
  <summary>Prerequisites</summary>

To complete the steps in this guide, you'll need:

- **The following in PingOne:**
  - An existing PingOne account
  - Organization admin permissions
- **To install the [`dagster-cloud` CLI](/dagster-plus/deployment/management/dagster-cloud-cli/installing-and-configuring)**
- **The following in Dagster+:**
  - A Pro plan
  - [Access to a user token](/dagster-plus/deployment/management/tokens/user-tokens)
  - [Organization Admin permissions](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions) in your organization

</details>

## Step 1: Add the Dagster+ app in PingOne \{#dagster-app}

1. Sign into your PingOne Console.
2. Using the sidebar, click **Connections > Applications**.

   ![PingOne Sidebar](/images/dagster-plus/features/authentication-and-access-control/pingone/sidebar.png)

3. On the **Applications** page, add an application.
4. In **Select an application type**, click **Web app**.
5. Click **SAML > Configure**:

   ![Add App](/images/dagster-plus/features/authentication-and-access-control/pingone/add-app.png)

## Step 2: Configure SSO in PingOne \{#configure-sso}

1.  In the **Create App Profile** page:

    1. Add an application name, description, and icon:

       ![Application Details](/images/dagster-plus/features/authentication-and-access-control/pingone/application-details.png)

    2. When finished, click **Save and Continue.**

2.  In the **Configure SAML** page:

    1.  Fill in the following:

        - **ACS URLs** and **Entity ID**: Copy and paste the following URL, replacing `<organization_name>` with your Dagster+ organization name:

          ```
          https://<organization_name>.dagster.cloud/auth/saml/consume
          ```

        - **Assertion Validity Duration**: Type `60`.
          In the following example, the organization's name is `hooli` and the Dagster+ domain is `https://hooli.dagster.cloud`:

        ![Service Provider Details](/images/dagster-plus/features/authentication-and-access-control/pingone/service-provider-details.png)

    2.  When finished, click **Save and Continue.**

3.  In the **Map Attributes** page:

    1. Configure the following attributes:

       | Application attribute | Outgoing value |
       | --------------------- | -------------- |
       | Email                 | Email Address  |
       | FirstName             | Given Name     |
       | LastName              | Family Name    |

       The page should look similar to the following:

       ![Attribute Mapping](/images/dagster-plus/features/authentication-and-access-control/pingone/attribute-mapping.png)

    2. When finished, click **Save and Continue.**

## Step 3: Upload the SAML metadata to Dagster+ \{#upload-saml}

Next, you'll save and upload the application's SAML metadata to Dagster+. This will enable single sign-on.

1. In PingOne, open the Dagster+ application.
2. Click the **Configuration** tab.
3. In the **Connection Details** section, click **Download Metadata**:

   ![SAML Metadata](/images/dagster-plus/features/authentication-and-access-control/pingone/saml-metadata.png)

4. When prompted, save the file to your computer.
5. After you've downloaded the SAML metadata file, upload it to Dagster+ using the `dagster-cloud` CLI:

   ```shell
   dagster-cloud organization settings saml upload-identity-provider-metadata <path/to/metadata> \
     --api-token=<user_token> \
     --url https://<organization_name>.dagster.cloud
   ```

## Step 4: Grant access to users \{#grant-access}

Next, you'll assign users to the Dagster+ application in PingOne. This will allow them to log in using their PingOne credentials when the single sign-on flow is initiated.

1. In the Dagster+ application, click the **Access** tab.
2. Click the **pencil icon** to edit the **Group membership policy**:

   ![Assign New Login](/images/dagster-plus/features/authentication-and-access-control/pingone/new-login.png)

3. Edit the policy as needed to grant users access to the application.

import TestSSO from '../../../../partials/\_TestSSO.md';

<TestSSO />

In the PingOne application portal, click the **Dagster+** icon:

![Identity Provider Login](/images/dagster-plus/features/authentication-and-access-control/pingone/identity-provider-login.png)

If successful, you'll be automatically signed in to your Dagster+ organization.
