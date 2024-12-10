---
layout: Integration
status: published
name: Secrets Manager
title: Dagster & AWS Secrets Manager
sidebar_label: Secrets Manager
excerpt: This integration allows you to manage, retrieve, and rotate credentials, API keys, and other secrets using AWS Secrets Manager.
date: 2024-06-21
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-aws
docslink:
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-secretsmanager.svg
categories:
  - Other
enabledBy:
enables:
---

### About this integration

This integration allows you to manage, retrieve, and rotate credentials, API keys, and other secrets using [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/).

### Installation

```bash
pip install dagster-aws
```

### Examples

<CodeExample filePath="integrations/aws-secretsmanager.py" language="python" />

### About AWS Secrets Manager

**AWS Secrets Manager** helps you protect access to your applications, services, and IT resources without the upfront cost and complexity of managing your own hardware security module infrastructure. With Secrets Manager, you can rotate, manage, and retrieve database credentials, API keys, and other secrets throughout their lifecycle. Users and applications retrieve secrets with a call to Secrets Manager APIs, eliminating the need to hardcode sensitive information in plain text.
