---
description: The Dagster+ agent interacts with a specific set of IP addresses that you may need to allowlist in your infrastructure.
sidebar_label: IP addresses
sidebar_position: 6000
title: Dagster+ IP addresses
tags: [dagster-plus-feature]
---

The Dagster+ web interface, CLI, and GraphQL API use [AWS Cloudfront's content delivery network](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/LocationsOfEdgeServers.html).

:::tip

If your organization requires that agent traffic stays entirely on the AWS private network, Dagster+ supports AWS PrivateLink as an alternative to IP allowlisting. To enable AWS PrivateLink, [contact the Dagster team](https://dagster.io/contact) to enable it. For details, see the [Hybrid architecture security overview](/deployment/dagster-plus/hybrid/architecture#private-connectivity-aws-privatelink).

:::

## IP addresses

The Dagster+ agent interacts with the following IP addresses:

<Tabs groupId="region">
  <TabItem value="us-region" label="US region">

```plain
34.215.239.157
35.165.239.109
35.83.161.124
44.236.154.129
44.236.31.202
44.239.93.251
54.185.29.42
54.188.126.120
```

  </TabItem>
  <TabItem value="eu-region" label="EU region">

```plain
13.50.180.120
13.51.19.57
13.60.164.107
13.62.96.222
13.62.107.201
51.21.15.208
```

  </TabItem>
</Tabs>

:::note
Additional IP addresses may be added over time. This list was last updated on **December 17, 2025**.
:::

## URLs

In addition to these IP addresses, the following URLs also need to be allowed egress access from your agent:

<Tabs groupId="region">
    <TabItem value="us-region" label="US region">
        - `cloud-prod-object-snapshots.s3.amazonaws.com` and `cloud-prod-object-snapshots.s3.us-west-2.amazonaws.com`
        - `cloud-prod-compute-logs.s3.amazonaws.com` and `cloud-prod-compute-logs.s3.us-west-2.amazonaws.com` \*
        - `<organization-name>.agent.dagster.cloud`
    </TabItem>
    <TabItem value="eu-region" label="EU region">
        - `cloud-prod-eu-object-snapshots.s3.amazonaws.com` and `cloud-prod-eu-object-snapshots.s3.eu-north-1.amazonaws.com`
        - `cloud-prod-eu-compute-logs.s3.amazonaws.com` and `cloud-prod-eu-compute-logs.s3.eu-north-1.amazonaws.com` \*
        - `<organization-name>.agent.eu.dagster.cloud`
    </TabItem>
</Tabs>

\* Only required if compute logs are being sent to Dagster+'s control plane. Not needed if you've configured compute logs to be sent to your own blob storage. See [Managing compute logs and error messages](/deployment/dagster-plus/management/managing-compute-logs-and-error-messages) for more details.

:::note

By default, the S3 URLs that Dagster+ generates for your agent use the legacy global S3 hostname (for example, `cloud-prod-object-snapshots.s3.amazonaws.com`). If your network requires regional S3 hostnames (for example, `cloud-prod-object-snapshots.s3.us-west-2.amazonaws.com`), such as when routing S3 traffic through an [AWS PrivateLink interface endpoint for S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/privatelink-interface-endpoints.html) that doesn't support legacy global endpoints, [contact the Dagster team](https://dagster.io/contact) to have your organization switched to regional-style URLs. If you allowlist hostnames, we recommend allowlisting both forms.

:::
