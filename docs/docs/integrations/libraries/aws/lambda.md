---
title: Dagster & AWS Lambda
sidebar_label: Lambda
sidebar_position: 7
description: Using this integration, you can leverage AWS Lambda to execute external code as part of your Dagster pipelines. This is particularly useful for running serverless functions that can scale automatically and handle various workloads without the need for managing infrastructure. The PipesLambdaClient class allows you to invoke AWS Lambda functions and stream logs and structured metadata back to Dagster's UI and tools.
tags: [dagster-supported, compute]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-lambda.svg
partnerlink: https://aws.amazon.com/
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-lambda.py" language="python" />

## About AWS Lambda

**AWS Lambda** is a serverless compute service provided by Amazon Web Services (AWS). It allows you to run code without provisioning or managing servers. AWS Lambda automatically scales your application by running code in response to each trigger, such as changes to data in an Amazon S3 bucket or an update to a DynamoDB table. You can use AWS Lambda to extend other AWS services with custom logic, or create your own backend services that operate at AWS scale, performance, and security.
