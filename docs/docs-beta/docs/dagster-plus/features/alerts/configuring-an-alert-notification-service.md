---
title: Configuring an alert notification service
sidebar_position: 100
---

Dagster+ allows you to configure alerts to fire in response to a range of events. These alerts can be sent to a variety of different services, depending on your organization's needs.

{/** TODO this needs content on the value prop of alerts -- save money, etc **/}

:::note
You must have **Organization**, **Admin**, or **Editor** permissions on Dagster+ to configure an alert notification service.
:::

Before [creating alerts](creating-alerts), you'll need to configure a service to send alerts. Dagster+ currently supports sending alerts through email, Microsoft Teams, PagerDuty, and Slack.

<Tabs groupId="notification_service">
  <TabItem value='email' label='Email'>
    No additional configuration is required to send emails from Dagster+.

All alert emails will be sent by `"no-reply@dagster.cloud"` or `"no-reply@<subdomain>.dagster.cloud"`. Alerts can be configured to be sent to any number of emails.

  </TabItem>
  <TabItem value='microsoft_teams' label='Microsoft Teams'>
    Create an incoming webhook by following the [Microsoft Teams documentation](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook?tabs=newteams%2Cdotnet).

This will provide you with a **webhook URL** which will be required when configuring alerts in the UI (after selecting "Microsoft Teams" as your Notification Service) or using the CLI (in the `notification_service` configuration).

  </TabItem>
  <TabItem value='pagerduty' label='PagerDuty'>
    :::note
You will need sufficient permissions in PagerDuty to add or edit services.
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

When setting up an alert, you can choose a Slack channel to send those alerts to. Make sure to invite the `@Dagster+` bot to any channel that you'd like to receive an alert in.

  </TabItem>
</Tabs>
