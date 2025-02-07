---
layout: Integration
status: published
name: Secrets Manager
title: Dagster & AWS Secrets Manager
sidebar_label: Secrets Manager
excerpt: This integration allows you to manage, retrieve, and rotate credentials, API keys, and other secrets using AWS Secrets Manager.
date: 2024-06-21
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-aws
docslink:
partnerlink: https://aws.amazon.com/
categories:
  - Other
enabledBy:
enables:
tags: [dagster-supported]
sidebar_custom_props:
  logo: images/integrations/aws-secretsmanager.svg
---

import Beta from '../../../partials/\_Beta.md';

<Beta />

This integration allows you to manage, retrieve, and rotate credentials, API keys, and other secrets using [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/).

### Installation

```bash
pip install dagster-aws
```

### Examples

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/aws-secretsmanager.py" language="python" />

### About AWS Secrets Manager

**AWS Secrets Manager** helps you protect access to your applications, services, and IT resources without the upfront cost and complexity of managing your own hardware security module infrastructure. With Secrets Manager, you can rotate, manage, and retrieve database credentials, API keys, and other secrets throughout their lifecycle. Users and applications retrieve secrets with a call to Secrets Manager APIs, eliminating the need to hardcode sensitive information in plain text.
