---
title: "Getting started with Dagster+"
displayed_sidebar: "dagsterPlus"
---

# Get started with Dagster+

First [create a Dagster+ organization](https://dagster.plus/signup). Note: you can sign up with:
- a Google email address
- a GitHub account
- a one-time email link, great if you are using a corporate email. You can setup SSO after completing these steps.

Next, pick your deployment type. Not sure?

- [Dagster+ Serverless](/dagster-plus/deployment/serverless) is the easiest way to get started and is great for teams with limited DevOps support. In Dagster+ Serverless, your Dagster code is executed in Dagster+. You will need to be okay [giving Dagster+ the credentials](/dagster-plus/deployment/environment-variables) to connect to the tools you want to orchestrate.

- [Dagster+ Hybrid](/dagster-plus/deployment/hybrid) is great for teams who want to orchestrate tools without giving Dagster+ direct access to your systems. Dagster+ Hybrid requires more DevOps support.

The remaining steps depend on your deployment type.

<Tabs>
<TabItem value="serverless" label="Dagster+ Serverless">

We recommend following the steps in Dagster+ to add a new project.

![Screenshot of Dagster+ serverless NUX](/img/placeholder.svg)

The Dagster+ on-boarding will guide you through:
- creating a Git repository containing your Dagster code
- setting up the necessary CI/CD actions to deploy that repository to Dagster+

:::tip
If you don't have any Dagster code yet, you will have the option to select an example quickstart project or import an existing dbt project
:::

See the guide on [adding code locations](/dagster-plus/deployment/code-locations) for details.
</TabItem>

<TabItem value="hybrid" label="Dagster+ Hybrid">

## Install a Dagster+ Hybrid agent

Follow [these guides](/dagster-plus/deployment/hybrid) for installing a Dagster+ Hybrid agent. Not sure which agent to pick? We recommend using the Dagster+ Kubernetes agent in most cases.


## Setup CI/CD

In most cases, your CI/CD process will be responsible for:
- building your Dagster code into a Docker image
- pushing your Docker image to a container registry you manage
- notifying Dagster+ of the new or updated code

Refer to the guide for [adding a code location](/dagster-plus/deployment/code-locations) for more detail.

</TabItem>
</Tabs>


## Next steps

Your Dagster+ account is automatically enrolled in a trial. You can [pick your plan type and enter your billing information](/dagster-plus/settings), or [contact the Dagster team](https://dagster.io/contact) if you need support or want to evaluate the Dagster+ Pro plan.
