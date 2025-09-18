---
description: How to set up Dagster+  Serverless in a HIPAA-compliant way
sidebar_label: HIPAA compliance
sidebar_position: 5000
title: HIPAA compliance in Dagster+ serverless
---

This guide covers setting up Dagster+ Serverless in a HIPAA compliant way.

:::warning Disclaimer

This is guidance only, not legal advice. Dagster Labs makes no HIPAA compliance guarantees. Consult legal or compliance professionals.

:::

## Prerequisites before processing protected health information (PHI)

- Execute a Business Associates Agreement (BAA) with Dagster Labs. (Contact your account representative or customer success manager.)
- Request access to our [Trust Center](https://app.vanta.com/dagsterlabs/trust/zyhc4hyugh7p1jlv6mnj6z) to review our security and compliance documents.
- Review the [Dagster+ Serverless security doc](/deployment/dagster-plus/serverless/security).
- Coordinate with your account representative or customer success manager to disable the default Serverless I/O manager.

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
