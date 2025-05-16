---
description: Configure Dagster+ alert notifications to trigger via email, Microsoft Teams, PagerDuty, or Slack.
sidebar_position: 100
title: Configuring an alert notification service
---

Dagster+ allows you to configure alerts to fire in response to a range of events. These alerts can be sent to a variety of different services, depending on your organization's needs.

:::note
You must have **Organization**, **Admin**, or **Editor** permissions on Dagster+ to configure an alert notification service.
:::

Before [creating alerts](/dagster-plus/features/alerts/creating-alerts), you'll need to configure a service to send alerts. Dagster+ currently supports sending alerts through email, Microsoft Teams, PagerDuty, and Slack.

<Tabs groupId="notification_service">
  <TabItem value='email' label='Email'>
    No additional configuration is required to send emails from Dagster+.

All alert emails will be sent by `"no-reply@dagster.cloud"` or `"no-reply@<subdomain>.dagster.cloud"`. Alerts can be configured to be sent to any number of emails.

  </TabItem>
  <TabItem value='microsoft_teams' label='Microsoft Teams'>
    Follow the [Microsoft Teams documentation](https://support.microsoft.com/en-us/office/create-incoming-webhooks-with-workflows-for-microsoft-teams-8ae491c7-0394-4861-ba59-055e33f75498) to create an incoming webhook with a workflow using a template. Dagster requires the workflow to allow anyone to trigger it (the default authentication type).

This will provide you with a **workflow URL** which will be required when configuring alerts in the UI (after selecting "Microsoft Teams" as your Notification Service) or using the CLI (in the `notification_service` configuration).

  </TabItem>
  <TabItem value='pagerduty' label='PagerDuty'>
    :::note
A Dagster+ Pro plan is required to use this feature. You will also need sufficient permissions in PagerDuty to add or edit services.
:::

In PagerDuty, you can either:

- [Create a new service](https://support.pagerduty.com/main/docs/services-and-integrations#create-a-service), and add Dagster+ as an integration, or
- [Edit an existing service](https://support.pagerduty.com/main/docs/services-and-integrations#edit-service-settings) to include Dagster+ as an integration

When configuring the integration, choose **Dagster+** as the integration type, and choose an integration name in the format `dagster-plus-{your_service_name}`.

After adding your new integration, you will be taken to a screen containing an **Integration Key**. This value will be required when configuring alerts in the UI (after selecting "PagerDuty" as your Notification Service) or using the CLI (in the `notification_service` configuration).

  </TabItem>
  <TabItem value='slack' label='Slack'>
    :::note
You will need sufficient permissions in Slack to add apps to your workspace.
:::
Navigate to **Deployment > Alerts** in the Dagster+ UI and click **Connect to Slack**. From there, you can complete the installation process.

When setting up an alert, you can choose a Slack channel to send those alerts to. Make sure to invite the `@Dagster Cloud` bot to any channel that you'd like to receive an alert in.

To disconnect Dagster+ from Slack, remove the Dagster Cloud app from your Slack workspace. For more information, see the [Slack documentation](https://slack.com/help/articles/360003125231-Remove-apps-and-custom-integrations-from-your-workspace#remove-an-app). If you are unable to do this, contact Dagster+ Support to disconnect it on your behalf.

  </TabItem>
</Tabs>
