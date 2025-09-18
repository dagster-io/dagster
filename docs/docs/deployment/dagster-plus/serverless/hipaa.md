---
description: How to setup Dagster+ serverless in a HIPAA compliant way
sidebar_label: HIPAA compliance
sidebar_position: 5000
title: HIPAA Compliance in Dagster+ serverless
---

You can use Dagster+ serverless in a HIPAA compliant way. This guide documents what you need to do to do so.

:::warning Disclaimer
This is guidance only, not legal advice. Dagster Labs makes no HIPAA compliance guarantees. Consult legal/compliance professionals.
:::

## Prerequisites before PHI processing

- Execute a Business Associates Agreement (BAA) with Dagster Labs (contact your account representative or customer success manager).
- Request access to our [Trust Center](https://app.vanta.com/dagsterlabs/trust/zyhc4hyugh7p1jlv6mnj6z) to review our security and compliance documents.
- Review security docs: [Dagster+ Serverless Security](/deployment/dagster-plus/serverless/security).
- Coordinate with your account representative or customer success manager to disable the default serverless I/O manager.

:::danger Important
You must disable the default I/O manager before processing any PHI. The default I/O manager is not HIPAA-compliant. Coordinate with Dagster Engineering through your account representative or customer success manager to ensure proper configuration.
:::

## Additional considerations

HIPAA compliance is an ongoing process that requires:

- Regular security assessments
- Comprehensive documentation of all configurations and processes
- Continuous monitoring and audit logging
- Staff training on HIPAA requirements

## Getting help

For questions about HIPAA compliance with Dagster+, contact your account representative or customer success manager.
