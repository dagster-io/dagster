---
description: The Dagster+ agent interacts with a specific set of IP addresses that you may need to allowlist in your infrastructure.
sidebar_label: IP addresses
sidebar_position: 6000
title: Dagster+ IP addresses
tags: [dagster-plus-feature]
---

The Dagster+ web interface, CLI, and GraphQL API use [AWS Cloudfront's content delivery network](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/LocationsOfEdgeServers.html).

## IP addresses

The Dagster+ agent interacts with the following IP addresses:

```
34.215.239.157
35.165.239.109
35.83.161.124
44.236.154.129
44.236.31.202
44.239.93.251
54.185.29.42
54.188.126.120
```

:::note
Additional IP addresses may be added over time. This list was last updated on **February 7, 2025**.
:::

## URLs

In addition to these IP addresses, the following URLs also need to be allowed egress access from your agent:

<Tabs>
    <TabItem value="us-region" label="US region">
        - `cloud-prod-object-snapshots.s3.amazonaws.com`
        - `cloud-prod-compute-logs.s3.amazonaws.com` - Only required if compute logs are being sent to Dagster+'s control plane. Not needed if you've configured compute logs to be sent to your own blob storage. See [Managing compute logs and error messages](/deployment/dagster-plus/management/managing-compute-logs-and-error-messages) for more details.
        - `<organization-name>.agent.dagster.cloud`
    </TabItem>
    <TabItem value="eu-region" label="EU region">
        - `cloud-prod-eu-object-snapshots.s3.amazonaws.com`
        - `cloud-prod-eu-compute-logs.s3.amazonaws.com` - Only required if compute logs are being sent to Dagster+'s control plane. Not needed if you've configured compute logs to be sent to your own blob storage. See [Managing compute logs and error messages](/deployment/dagster-plus/management/managing-compute-logs-and-error-messages) for more details.
        - `<organization-name>.agent.eu.dagster.cloud`
    </TabItem>
</Tabs>
