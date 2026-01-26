---
title: PII redaction in compute logs
description: How to redact personally identifiable information (PII) from Dagster compute logs.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore how to protect sensitive data by redacting personally identifiable information (PII) from Dagster [compute logs](/guides/log-debug/logging). When your pipelines process customer data, logs may inadvertently capture sensitive information like emails, phone numbers, or social security numbers. A custom compute log manager can automatically redact this data before it's displayed in the UI.

## Problem: Sensitive data in logs

Imagine your assets process customer records, and debugging statements or error messages include PII. Without protection, this sensitive data would be visible to anyone with access to the Dagster UI, potentially violating privacy regulations like GDPR or HIPAA.

Consider an asset that logs customer information during processing:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/pii_compute_logs/example_asset.py"
  language="python"
  title="src/project_mini/defs/pii_compute_logs/example_asset.py"
/>

Without redaction, the logs would display all sensitive information:

```
Processing data for customer: John Doe
Email: john.doe@example.com
Phone: 555-123-4567
SSN: 123-45-6789
Credit Card: 4111-1111-1111-1111
IP Address: 192.168.1.100
```

## Shared component: PII redactor

Both solutions use a PII redactor that identifies and masks sensitive data using regex patterns for common PII types:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/pii_compute_logs/pii_redactor.py"
  language="python"
  title="src/project_mini/defs/pii_compute_logs/pii_redactor.py"
/>

## Solution 1: Redact on read

The first approach redacts PII when logs are read for display. This preserves the original unredacted logs on disk, which can be useful for debugging or audit purposes.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/pii_compute_logs/pii_compute_log_manager.py"
  language="python"
  title="src/project_mini/defs/pii_compute_logs/pii_compute_log_manager.py"
/>

Configure this approach in your `dagster.yaml`:

```yaml
compute_logs:
  module: your_project.pii_compute_log_manager
  class: PIIComputeLogManager
  config:
    base_dir: compute_logs
    redact_for_ui: true
```

|                      | **Redact on read**                                       |
| -------------------- | -------------------------------------------------------- |
| **Storage**          | Original logs preserved on disk                          |
| **Security**         | PII exists on disk; redacted only in UI                  |
| **Debugging**        | Administrators can access unredacted logs if needed      |
| **Cloud deployment** | Additional handling needed to redact before cloud upload |

## Solution 2: Redact on write

For maximum security, redact PII as logs are written to disk. This ensures sensitive data never reaches storage, but means the original data cannot be recovered.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/pii_compute_logs/pii_log_manager_write.py"
  language="python"
  title="src/project_mini/defs/pii_compute_logs/pii_log_manager_write.py"
/>

Configure this approach in your `dagster.yaml`:

```yaml
compute_logs:
  module: your_project.pii_log_manager_write
  class: PIIComputeLogManagerWrite
  config:
    base_dir: compute_logs
    redact_on_write: true
```

|                      | **Redact on write**                      |
| -------------------- | ---------------------------------------- |
| **Storage**          | Only redacted logs stored                |
| **Security**         | Maximum security; PII never reaches disk |
| **Debugging**        | Original data cannot be recovered        |
| **Cloud deployment** | Works seamlessly; logs are pre-redacted  |

## Choosing an approach

| Consideration        | Redact on read | Redact on write |
| -------------------- | -------------- | --------------- |
| **Security level**   | Moderate       | Maximum         |
| **Original access**  | Yes            | No              |
| **Setup complexity** | Low            | Low             |
| **Cloud-ready**      | Needs handling | Yes             |
