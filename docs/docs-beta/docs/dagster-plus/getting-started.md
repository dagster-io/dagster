---
title: "Getting started with Dagster+"
---

To get started with Dagster+, you will need to create a Dagster+ organization and choose your deployment type (Serverless or Hybrid).

## Create a Dagster+ organization

First, [create a Dagster+ organization](https://dagster.plus/signup). You can sign up with:
- a Google email address
- a GitHub account
- a one-time email link (ideal if you are using a corporate email). You can set up SSO after completing these steps.

## Choose your deployment type

- [Dagster+ Serverless](/dagster-plus/deployment/deployment-types/serverless) is the easiest way to get started and is great for teams with limited DevOps support. In Dagster+ Serverless, your Dagster code is executed in Dagster+. You will need to be okay [giving Dagster+ the credentials](/dagster-plus/deployment/management/environment-variables) to connect to the tools you want to orchestrate.

- [Dagster+ Hybrid](/dagster-plus/deployment/deployment-types/hybrid) is great for teams who want to orchestrate tools without giving Dagster+ direct access to your systems. Dagster+ Hybrid requires more DevOps support.

The remaining steps depend on your deployment type.

<Tabs>
<TabItem value="serverless" label="Dagster+ Serverless">

We recommend following the steps in Dagster+ to add a new project.

The Dagster+ onboarding will guide you through:
- creating a Git repository containing your Dagster code
- setting up the necessary CI/CD actions to deploy that repository to Dagster+

:::tip
If you don't have any Dagster code yet, you can select an example project or import an existing dbt project.
:::

See the guide on [adding code locations](/dagster-plus/deployment/code-locations) for details.
</TabItem>

<TabItem value="hybrid" label="Dagster+ Hybrid">

**Install a Dagster+ Hybrid agent**

Follow [these guides](/dagster-plus/deployment/deployment-types/hybrid) for installing a Dagster+ Hybrid agent. If you're not sure which agent to use, we recommend the [Dagster+ Kubernetes agent](/dagster-plus/deployment/deployment-types/hybrid/kubernetes/index.md) in most cases.


**Set up CI/CD**

In most cases, your CI/CD process will be responsible for:
- building your Dagster code into a Docker image
- pushing your Docker image to a container registry you manage
- notifying Dagster+ of the new or updated code

Refer to the guide for [adding a code location](/dagster-plus/deployment/code-locations) for more detail.

</TabItem>
</Tabs>


## Next steps

Your Dagster+ account is automatically enrolled in a trial. You can [pick your plan type and enter your billing information](/dagster-plus/deployment/management/settings/dagster-plus-settings), or [contact the Dagster team](https://dagster.io/contact) if you need support or want to evaluate the Dagster+ Pro plan.
