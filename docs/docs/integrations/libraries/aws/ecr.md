---
title: Dagster & AWS ECR
sidebar_label: ECR
description: This integration allows you to connect to AWS Elastic Container Registry (ECR), enabling you to manage your container images more effectively in your Dagster pipelines.
tags: [dagster-supported]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-ecr.svg
partnerlink: https://aws.amazon.com/
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

This integration allows you to connect to AWS Elastic Container Registry (ECR). It provides resources to interact with AWS ECR, enabling you to manage your container images.

Using this integration, you can seamlessly integrate AWS ECR into your Dagster pipelines, making it easier to manage and deploy containerized applications.

### Installation

```bash
pip install dagster-aws
```

### Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-ecr.py" language="python" />

### About AWS ECR

AWS Elastic Container Registry (ECR) is a fully managed Docker container registry that makes it easy for developers to store, manage, and deploy Docker container images. AWS ECR is integrated with Amazon Elastic Kubernetes Service (EKS), simplifying your development to production workflow. With ECR, you can securely store and manage your container images and easily integrate with your existing CI/CD pipelines. AWS ECR provides high availability and scalability, ensuring that your container images are always available when you need them.
