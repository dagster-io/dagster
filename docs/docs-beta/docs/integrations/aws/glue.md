---
layout: Integration
status: published
name: Glue
title: Dagster & AWS Glue
sidebar_label: Glue
excerpt: The AWS Glue integration enables you to initiate AWS Glue jobs directly from Dagster, seamlessly pass parameters to your code, and stream logs and structured messages back into Dagster.
date: 2024-08-20
apireflink: https://docs.dagster.io/concepts/dagster-pipes/aws-glue
docslink:
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-glue.svg
categories:
  - Compute
enabledBy:
enables:
---

### About this integration

The `dagster-aws` integration library provides the `PipesGlueClient` resource, enabling you to launch AWS Glue jobs directly from Dagster assets and ops. This integration allows you to pass parameters to Glue code while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated jobs. With minimal code changes required on the job side, this integration is both efficient and easy to implement.

### Installation

```bash
pip install dagster-aws
```

### Examples

<CodeExample filePath="integrations/aws-glue.py" language="python" />

### About AWS Glue

**AWS Glue** is a fully managed cloud service designed to simplify and automate the process of discovering, preparing, and integrating data for analytics, machine learning, and application development. It supports a wide range of data sources and formats, offering seamless integration with other AWS services. AWS Glue provides the tools to create, run, and manage ETL (Extract, Transform, Load) jobs, making it easier to handle complex data workflows. Its serverless architecture allows for scalability and flexibility, making it a preferred choice for data engineers and analysts who need to process and prepare data efficiently.
