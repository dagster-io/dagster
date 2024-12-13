---
title: 'OneLogin SSO'
sidebar_position: 500
---

In this guide, you'll configure OneLogin to use single sign-on (SSO) with your Dagster+ organization.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **The following in OneLogin:**
  - An existing OneLogin account
  - Admin permissions
- **To install the [`dagster-cloud` CLI](/todo)**
- **The following in Dagster+:**
  - A Pro plan
  - [Access to a user token](/todo)
  - [Organization Admin permissions](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions) in your organization

</details>

## Step 1: Add the Dagster+ app in OneLogin \{#dagster-app}

1. Sign into your OneLogin portal.
2. Navigate to **Administration > Applications**.
3. On the **Applications** page, click **Add App**.
4. On the **Find Applications** page, search for `Dagster+`:

   ![Find Applications in OneLogin](/img/placeholder.svg)

5. Add and save the application.

## Step 2: Configure SSO in OneLogin \{#configure-sso}

1. In OneLogin, open the application and navigate to its **Configuration**.
2. In the **Dagster+ organisation name** field, enter your Dagster+ organization name. This is used to route the SAML response to the correct Dagster+ subdomain.

   For example, your organization name is `hooli` and your Dagster+ domain is `https://hooli.dagster.cloud`. To configure this correctly, you'd enter `hooli` into the **Subdomain** field.

3. When finished, click **Done**.

## Step 3: Upload the SAML metadata to Dagster+ \{#upload-saml}

Next, you'll save and upload the application's SAML metadata to Dagster+. This will enable single sign-on.

1. In OneLogin, open the Dagster+ application.
2. Navigate to **More Actions > SAML Metadata**.
3. When prompted, save the file to your computer.
4. After you've downloaded the SAML metadata file, upload it to Dagster+ using the `dagster-cloud` CLI:

   ```shell
   dagster-cloud organization settings saml upload-identity-provider-metadata <path/to/metadata> \
     --api-token=<user_token> \
     --url https://<organization_name>.dagster.cloud
   ```

## Step 4: Grant access to users \{#grant-access}

Next, you'll assign users to the Dagster+ application in OneLogin. This will allow them to log in using their OneLogin credentials with the sign in flow is initiated.

1. In Okta, navigate to **Users**.
2. Select a user.
3. On the user's page, click **Applications**.
4. Assign the user to Dagster+. In the following image, the user `Test D'Test` has been assigned to Dagster+:

   ![Screenshot of Assign New Login in OneLogin](/img/placeholder.svg)

5. Click **Continue**.
6. Click **Save User.**
7. Repeat steps 2-6 for every user you want to access Dagster+.

import TestSSO from '../../../../partials/\_TestSSO.md';

<TestSSO />

In the OneLogin portal, click the Dagster+ icon:

![Screenshot of the Dagster+ icon in OneLogin](/img/placeholder.svg)

If successful, you'll be automatically signed into your Dagster+ organization.
