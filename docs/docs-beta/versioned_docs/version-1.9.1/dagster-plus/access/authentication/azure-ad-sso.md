---
title: 'Azure Active Directory SSO'
displayed_sidebar: 'dagsterPlus'
---

# Setting up Azure Active Directory SSO for Dagster+

In this guide, you'll configure Azure Active Directory (AD) to use single sign-on (SSO) with your Dagster+ organization.

<details>
  <summary>Prerequisites</summary>

To complete the steps in this guide, you'll need:

- **An existing Azure AD account**
- **To install the [`dagster-cloud` CLI](/todo)**
- **The following in Dagster+:**
  - A Pro plan
  - [Access to a user token](/todo)
  - [Organization Admin permissions](/dagster-plus/access/rbac/user-roles-permissions) in your organization

</details>

## Step 1: add the Dagster+ app in Azure AD \{#dagster-app}

In this step, you'll add the Dagster+ app to your list of managed SaaS apps in Azure AD.

1. Sign in to the Azure portal.
2. On the left navigation pane, click the **Azure Active Directory** service.
3. Navigate to **Enterprise Applications** and then **All Applications**.
4. Click **New application**.
5. In the **Add from the gallery** section, type **Dagster+** in the search box.
6. Select **Dagster+** from the results panel and then add the app. Wait a few seconds while the app is added to your tenant.

## Step 2: configure SSO in Azure AD \{#configure-sso}

In this step, you'll configure and enable SSO for Azure AD in your Azure portal.

1.  On the **Dagster+** application integration page, locate the **Manage** section and select **single sign-on**.
2.  On the **Select a single sign-on method** page, select **SAML**.
3.  On the **Set up single sign-on with SAML** page, click the pencil icon for **Basic SAML Configuration** to edit the settings.
    ![Settings Dropdown](/img/placeholder.svg)
4.  In the **Basic SAML Configuration** section, fill in the **Identifier** and **Reply URL** fields as follows:

    Copy and paste the following URL, replacing `<organization_name>` with your Dagster+ organization name:

    ```
    https://<organization_name>.dagster.cloud/auth/saml/consume
    ```

5.  Click **Set additional URLs**.
6.  In the **Sign-on URL** field, copy and paste the URL you entered in the **Identifier** and **Reply URL** fields.
7.  Next, you'll configure the SAML assertions. In addition to the default attributes, Dagster+ requires the following:

    - `FirstName` - `user.givenname`
    - `LastName` - `user.surname`
    - `Email` - `user.userprincipalname`

    Add these attribute mappings to the SAML assertion.
8.  On the **Set up single sign-on with SAML** page:
    1. Locate the **SAML Signing Certificate** section.
    2. Next to **Federation Metadata XML**, click **Download**:

       ![Download SAML Certificate](/img/placeholder.svg)

    When prompted, save the SAML metadata file to your computer.

## Step 3: upload the SAML metadata to Dagster+ \{#upload-saml}

After you've downloaded the SAML metadata file, upload it to Dagster+ using the `dagster-cloud` CLI:

```shell
dagster-cloud organization settings saml upload-identity-provider-metadata <path/to/metadata> \
   --api-token=<user_token> \
   --url https://<organization_name>.dagster.cloud
```

## Step 4: create a test user \{#test-user}

In this section, you'll create a test user in the Azure portal.

1. From the left pane in the Azure portal, click **Azure Active Directory**.
2. Click **Users > All users**.
3. Click **New user** at the top of the screen.
4. In **User** properties, fill in the following fields:
   - **Name**: Enter `B.Simon`.
   - **User name**: Enter `B.Simon@contoso.com`.
   - Select the **Show password** checkbox and write down the value displayed in the **Password** box.
5. Click **Create**.

import TestSSO from '../../../partials/\_TestSSO.md';

<TestSSO />

Click **Test this application** in the Azure portal. If successful, you'll be automatically signed into your Dagster+ organization.
