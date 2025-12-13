---
title: Dagster & AWS CloudWatch
sidebar_label: CloudWatch
sidebar_position: 3
description: This integration allows you to send Dagster logs to AWS CloudWatch, enabling centralized logging and monitoring of your Dagster jobs. By using AWS CloudWatch, you can take advantage of its powerful log management features, such as real-time log monitoring, log retention policies, and alerting capabilities.
tags: [dagster-supported, monitoring]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-cloudwatch.svg
partnerlink: https://aws.amazon.com/
---

import Deprecated from '@site/docs/partials/\_Deprecated.md';

<Deprecated />

<p>{frontMatter.description}</p>

Using this integration, you can configure your Dagster jobs to log directly to AWS CloudWatch, making it easier to track and debug your workflows. This is particularly useful for production environments where centralized logging is essential for maintaining observability and operational efficiency.

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-cloudwatch.py" language="python" />

## About AWS CloudWatch

AWS CloudWatch is a monitoring and observability service provided by Amazon Web Services (AWS). It allows you to collect, access, and analyze performance and operational data from a variety of AWS resources, applications, and services. With AWS CloudWatch, you can set up alarms, visualize logs and metrics, and gain insights into your infrastructure and applications to ensure they're running smoothly.

AWS CloudWatch provides features such as:

- Real-time monitoring: Track the performance of your applications and infrastructure in real-time.
- Log management: Collect, store, and analyze log data from various sources.
- Alarms and notifications: Set up alarms to automatically notify you of potential issues.
- Dashboards: Create custom dashboards to visualize metrics and logs.
- Integration with other AWS services: Seamlessly integrate with other AWS services for a comprehensive monitoring solution.
