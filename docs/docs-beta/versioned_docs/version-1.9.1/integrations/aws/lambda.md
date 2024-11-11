---
layout: Integration
status: published
name: Lambda
title: Dagster & AWS Lambda
sidebar_label: Lambda
excerpt: Using the AWS Lambda integration with Dagster, you can leverage serverless functions to execute external code in your pipelines.
date: 2024-06-21
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-aws
docslink:
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-lambda.svg
categories:
  - Compute
enabledBy:
enables:
---

### About this integration

Using this integration, you can leverage AWS Lambda to execute external code as part of your Dagster pipelines. This is particularly useful for running serverless functions that can scale automatically and handle various workloads without the need for managing infrastructure. The `PipesLambdaClient` class allows you to invoke AWS Lambda functions and stream logs and structured metadata back to Dagster's UI and tools.

### Installation

```bash
pip install dagster-aws
```

### Examples

<CodeExample filePath="integrations/aws-lambda.py" language="python" />

### About AWS Lambda

**AWS Lambda** is a serverless compute service provided by Amazon Web Services (AWS). It allows you to run code without provisioning or managing servers. AWS Lambda automatically scales your application by running code in response to each trigger, such as changes to data in an Amazon S3 bucket or an update to a DynamoDB table. You can use AWS Lambda to extend other AWS services with custom logic, or create your own backend services that operate at AWS scale, performance, and security.
