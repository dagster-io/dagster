---
title: Installing and configuring the dagster-cloud CLI
sidebar_position: 100
---

:::note
This guide is applicable to Dagster+.
:::

The `dagster-cloud` CLI is a command-line toolkit designed to work with Dagster+.

In this guide, we'll cover how to install and configure the `dagster-cloud` CLI, get help, and use some helpful environment variables and CLI options.

## Installing the CLI

The Dagster+ Agent library is available in PyPi. To install, run:

```shell
pip install dagster-cloud
```

Refer to the [configuration section](#configuring-the-cli) for next steps.

### Completions

Optionally, you can install command-line completions to make using the `dagster-cloud` CLI easier.

To have the CLI install these completions to your shell, run:

```shell
dagster-cloud --install-completion
```

To print out the completion for copying or manual installation:

```shell
dagster-cloud --show-completion
```

## Configuring the CLI

The recommended way to set up your CLI's config for long-term use is through the configuration file, located by default at `~/.dagster_cloud_cli/config`.

### Setting up the configuration file

Set up the config file:

```shell
dagster-cloud config setup
```

Select your authentication method. **Note**: Browser authentication is the easiest method to configure.

<details>
<summary><strong>BROWSER AUTHENTICATION</strong></summary>

The easiest way to set up is to authenticate through the browser.

```shell
$ dagster-cloud config setup
? How would you like to authenticate the CLI? (Use arrow keys)
 » Authenticate in browser
   Authenticate using token
Authorized for organization `hooli`

? Default deployment: prod
```

When prompted, you can specify a default deployment. If specified, a deployment won't be required in subsequent `dagster-cloud` commands. The default deployment for a new Dagster+ organization is `prod`.

</details>

<details>
<summary><strong>TOKEN AUTHENTICATION</strong></summary>

Alternatively, you may authenticate using a user token. Refer to the [User tokens guide](/dagster-plus/deployment/management/tokens) for more info.

```shell
$ dagster-cloud config setup
? How would you like to authenticate the CLI? (Use arrow keys)
   Authenticate in browser
 » Authenticate using token

? Dagster+ organization: hooli
? Dagster+ user token: *************************************
? Default deployment: prod
```

When prompted, specify the following:

- **Organization** - Your organization name as it appears in your Dagster+ URL. For example, if your Dagster+ instance is `https://hooli.dagster.cloud/`, this would be `hooli`.
- **User token** - The user token.
- **Default deployment** - **Optional**. A default deployment. If specified, a deployment won't be required in subsequent `dagster-cloud` commands. The default deployment for a new Dagster+ organization is `prod`.

</details>

### Viewing and modifying the configuration file

To view the contents of the CLI configuration file, run:

```shell
$ dagster-cloud config view

default_deployment: prod
organization: hooli
user_token: '*******************************8214fe'
```

Specify the `--show-token` flag to show the full user token.

To modify the existing config, re-run:

```shell
dagster-cloud config setup
```

## Toggling between deployments

To quickly toggle between deployments, run:

```shell
dagster-cloud config set-deployment <deployment_name>
```

## Getting help

To view help options in the CLI:

```shell
dagster-cloud --help
```
