# Using Dagster+ serverless in a HIPAA compliant way

:::warning Disclaimer
This is guidance only, not legal advice. Dagster Labs makes no HIPAA compliance guarantees. Consult legal/compliance professionals.
:::

You can use Dagster+ serverless in a HIPAA compliant way. This guide documents what you need to do to do so.

## Prerequisites before PHI processing

- Execute a Business Associates Agreement (BAA) with Dagster Labs (contact your account representative or customer success manager).
- Request Access to our [Trust Center](https://app.vanta.com/dagsterlabs/trust/zyhc4hyugh7p1jlv6mnj6z) to review our secuirty and compliance documents.
- Review security docs: [Dagster+ Serverless Security](/deployment/dagster-plus/serverless/security).
- Coordinate with your account representative or customer success manager to disable the default serverless I/O manager.

:::danger Important
Must disable default I/O manager - coordinate with Dagster Engineering before processing any PHI. The default I/O manager is not HIPAA-compliant.
:::

:::note Remember
HIPAA compliance is ongoing - regular assessments, documentation, and monitoring required.

Contact your account representative or customer success manager with any questions.
:::
