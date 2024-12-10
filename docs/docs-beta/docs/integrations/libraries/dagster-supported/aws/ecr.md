---
layout: Integration
status: published
name: ECR
title: Dagster & AWS ECR
sidebar_label: ECR
excerpt: This integration allows you to connect to AWS Elastic Container Registry (ECR), enabling you to manage your container images more effectively in your Dagster pipelines.
date: 2024-06-21
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-aws
docslink:
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-ecr.svg
categories:
  - Other
enabledBy:
enables:
---

### About this integration

This integration allows you to connect to AWS Elastic Container Registry (ECR). It provides resources to interact with AWS ECR, enabling you to manage your container images.

Using this integration, you can seamlessly integrate AWS ECR into your Dagster pipelines, making it easier to manage and deploy containerized applications.

### Installation

```bash
pip install dagster-aws
```

### Examples

<CodeExample filePath="integrations/aws-ecr.py" language="python" />

### About AWS ECR

AWS Elastic Container Registry (ECR) is a fully managed Docker container registry that makes it easy for developers to store, manage, and deploy Docker container images. AWS ECR is integrated with Amazon Elastic Kubernetes Service (EKS), simplifying your development to production workflow. With ECR, you can securely store and manage your container images and easily integrate with your existing CI/CD pipelines. AWS ECR provides high availability and scalability, ensuring that your container images are always available when you need them.
