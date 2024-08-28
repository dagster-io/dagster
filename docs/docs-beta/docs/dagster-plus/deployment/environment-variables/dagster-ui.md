---
title: "Set environment variables with the Dagster+ UI"
displayed_sidebar: "dagsterPlus"
sidebar_position: 1
sidebar_label: "Set with Dagster+ UI"
---

Environment variable are key-value pairs that are set outside of your source code. Using environment variables lets you dynamically change the behavior of your application without modifying source code and securely set up secrets.

Dagster supports several approaches for [accessing environment variable in your code](/todo). You can also set environment variables in several ways. This guide will cover how to set environment variables in the Dagster+ UI.

## What you'll learn

- How to add, edit, and delete environment variables in the Dagster+ UI
- How to modify the value of environment variables based on the deployment environment
- How to export environment variables for local use

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **Organization Admin**, **Admin**, or **Editor** permissions for your Dagster+ account
- To be using Dagster version 1.0.17 or later

</details>

## How to find the environment variables page
1. Sign in to your Dagster+ account
2. Use the deployment switcher in the top right corner to select the deployment where you want to view or manage environment variables
3. Navigate to the **Deployment** -> **Environment variables** page

## How to add an environment variable
To create a new environment variable:

1. [Navigate to the environment variables page](#how-to-find-the-environment-variables-page)
2. Click the **+ Add environment variable** button
3. A modal will open, fill out the following information
    - **Name** - Enter a name for the environment variable. This is how the variable will be referenced in your code.
    - **Value** - Enter a value for the environment variable.
    - **Deployment Scope** - select the deployment(s) where the variable should be accessible:
        - **Full deployment** - The variable will be available to selected code locations in the full deployment
        - **Branch deployments** - The variable will be available to selected code locations in Branch Deployments
        - **Local** - If selected, the variable will be included when [exporting environment variables to a local `.env` file](#how-to-export-environment-variables-locally)
    - **Code Location Scope** - select the code location(s) where the variable should be accessible. At least one code location is required.

<!-- TODO SCREENSHOT -->

4. Click **Save**

## How to edit an environment variable
To edit an existing environment variable:

1. [Navigate to the environment variables page](#how-to-find-the-environment-variables-page)
2. Click the **Edit** button on the right of the environment variable you want to edit
3. A modal will open where you can edit the attributes of the environment variable
4. Click **Save**

## How to delete an environment variable
To delete an environment variable:

1. [Navigate to the environment variables page](#how-to-find-the-environment-variables-page)
2. Click the **Trash icon** on the right of the environment variable you want to delete
3. A modal will open to confirm that you want to delete the environment variable. Click **Yes, delete** to delete the environment variable, or **Cancel** to close the modal and not delete the environment variable.

## How to view the value an environment variable
To view the value of an environment variable:

1. [Navigate to the environment variables page](#how-to-find-the-environment-variables-page)
2. Click the **eye icon** in the **Value** column of the environment variable you want to view
3. Click the **eye icon** again to hide the value.

:::note
Viewing an environment variable only reveals the value to you. It doesn't show the value in plaintext to all users. If you navigate away from the environment variables page or reload the page, the value will be hidden again.
:::



## How to add an environment variable for a Branch Deployment
If you want to give branch deployments access to an existing environment variable:

1. [Navigate to the environment variables page](#how-to-find-the-environment-variables-page)
2. Click the **Edit** button on the right of the environment variable you want to edit
3. A modal will open. Click the **Branch deployments** check-box to allow branch deployments to access the environment variable
4. Click **Save**

If you want to provide branch deployments a different value for the same environment variable key, see [How to set different values for environment variables in different deployment environments](#how-to-set-different-values-for-environment-variables-in-different-deployment-environments)



## How to export environment variables locally
You can export environment variables that have the **Local** scope selected into a `.env` file to use locally.

To download the file:
1. [Navigate to the environment variables page](#how-to-find-the-environment-variables-page)
2. Click the **arrow menu** to the right of the **+ Add environment variable** button
3. Click **Download local environment variables**. A file named `env.txt` will be downloaded

To use the downloaded environment variables for local Dagster development:
1. Rename the downloaded `env.txt` file to `.env`
2. Move the file to the directory where you run `dagster dev` or `dagster-webserver`
3. Run `dagster dev` or `dagster-webserver`
4. Confirm that the environment variables have been loaded by locating a log message that begins with `Loaded environment variables from .env file`


## How to set different values for environment variables in different deployment environments
You can create multiple instances of the same environment variable key with different values. This allows you to provide different values to different deployment environments. For example, you may want to use different Snowflake credentials for your production deployment than in branch deployments.

When you [add an environment variable](#how-to-add-an-environment-variable) you can select the deployment scope and code location scope for the environment variable. You can create multiple environment variables with different values and different scopes to customize the values in different deployment environments.

For example, if you wanted to provide different Snowflake password for your production deployment than in branch deployments, you would make two environment variables with the same key. For the production environment variable, you set the value for the production password and ensure the **Full deployment** box is checked and the **Branch deployments** box isn't checked. For the branch deployment environment variable, you set the value for the branch deployment password and ensure the **Branch deployments** box is checked and the **FullDeployment** box isn't checked.

<!-- TODO SCREENSHOT -->


## Next steps

- Learn how to [access environment variables in Dagster code](/todo)
- See the [built-in environment variables](https://docs.dagster.io/dagster-plus/managing-deployments/environment-variables-and-secrets#built-in-environment-variables) provided by Dagster
