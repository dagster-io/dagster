---
title: "Setting environment variables with the Dagster+ UI"
displayed_sidebar: "dagsterPlus"
sidebar_position: 1
sidebar_label: "Set with Dagster+ UI"
---

Environment variable are key-value pairs that are set outside of your source code. Using environment variables lets you dynamically change the behavior of your application without modifying source code and securely set up secrets.

Dagster supports several approaches for [accessing environment variable in your code](/todo). You can also set environment variables in several ways, but this guide will focus on the Dagster+ UI.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **Organization Admin**, **Admin**, or **Editor** permissions for your Dagster+ account
- To be using Dagster version 1.0.17 or later

</details>

## Adding environment variables \{#add}

Before you begin, use the deployment switcher to select the right deployment.

1. Click the **+ Add environment variable** button.
2. In the modal that displays, fill in the following:
    - **Name** - Enter a name for the environment variable. This is how the variable will be referenced in your code.
    - **Value** - Enter a value for the environment variable.
    - **Deployment Scope** - select the deployment(s) where the variable should be accessible:
        - **Full deployment** - The variable will be available to selected code locations in the full deployment.
        - **Branch deployments** - The variable will be available to selected code locations in Branch Deployments.
        - **Local** - If selected, the variable will be included when [exporting environment variables to a local `.env` file](#export).
    - **Code Location Scope** - select the code location(s) where the variable should be accessible. At least one code location is required.


{/* TODO replace placeholder image */}

![Screenshot of adding environment variables](/img/placeholder.svg)

3. Click **Save**

## Editing environment variables \{#edit}

On the **Environment variables** page, edit an environment variable by clicking the **Edit** button in the **Actions** column.

## Deleting environment variables \{#delete}

On the **Environment variables** page, delete an environment variable by clicking the **Trash icon** in the **Actions** column.

## Viewing environment variable values \{#view}

On the **Environment variables** page, view an environment variable by clicking the **eye icon** in the **Value** column. To hide the value, click the **eye icon** again.

:::note
Viewing an environment variable only reveals the value to you. It doesn't show the value in plaintext to all users. If you navigate away from the environment variables page or reload the page, the value will be hidden again.
:::

## Exporting environment variables locally \{#export}

1. On the **Environment variables** page, click the **arrow menu** to the right of the **+ Add environment variable** button.
2. Click **Download local environment variables**.
3. A file named `env.txt` will be downloaded.

To use the downloaded environment variables for local Dagster development:

1. Rename the downloaded `env.txt` file to `.env`.
2. Move the file to the directory where you run `dagster dev` or `dagster-webserver`.
3. Run `dagster dev`.

If the environment variables were loaded successfully, you'll see a log message that begins with `Loaded environment variables from .env file`.

## Setting environment-dependent variable values \{#environment-dependent-values}

You can create multiple instances of the same environment variable key with different values, allowing you to provide different values to different deployment environments. For example, you may want to use different Snowflake credentials for your production deployment than in branch deployments.

When you [add an environment variable](#add), you can select the deployment scope and code location scope for the environment variable. You can create multiple environment variables with different values and different scopes to customize the values in different deployment environments.

For example, if you wanted to provide different Snowflake passwords for your production and branch deployments, you would make two environment variables with the same key:

- For the **production** environment variable:
   - Set the value as the production password, and
   - Check only the **Full deployment** box
- For the **branch deployment** environment variable:
   - Set the value as the branch deployment password, and
   - Check only the **Branch deployments** box

![Screenshot of environment variables](/img/placeholder.svg)

## Next steps

- Learn how to [access environment variables in Dagster code](/todo)
- Learn about the [built-in environment variables](https://docs.dagster.io/dagster-plus/managing-deployments/environment-variables-and-secrets#built-in-environment-variables) provided by Dagster+
