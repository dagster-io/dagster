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

| Solution                                       | Best for                                                            |
| ---------------------------------------------- | ------------------------------------------------------------------- |
| [Redact on read](#solution-1-redact-on-read)   | Preserving originals on disk for debugging while redacting in UI    |
| [Redact on write](#solution-2-redact-on-write) | Maximum security; PII never reaches disk; works seamlessly in cloud |

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

The first approach redacts PII when logs are read for display, preserving the original unredacted logs on disk. This is useful when administrators need access to original logs for debugging or audit purposes, but requires additional handling in cloud deployments since files must be redacted before upload.

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

## Solution 2: Redact on write

For maximum security, redact PII as logs are written to disk. This ensures sensitive data never reaches storage and works seamlessly in cloud deployments since logs are pre-redacted. The trade-off is that original data cannot be recovered if needed for debugging.

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

:::tip Using ML-based detection

For production deployments with stricter compliance requirements, consider using [Microsoft Presidio](https://microsoft.github.io/presidio/) for ML-based PII detection. Presidio provides higher accuracy and supports 30+ entity types including international formats. Replace the regex-based `redact_pii` function with:

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def redact_pii(text: str) -> str:
    results = analyzer.analyze(text=text, language="en")
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text
```

:::
