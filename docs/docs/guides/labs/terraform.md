---
title: Managing Dagster+ with Terraform
description: Use the Dagster+ Terraform provider to manage your organization's deployments, users, teams, secrets, and alerts as infrastructure-as-code.
tags: [dagster-plus-feature]
canonicalUrl: '/guides/labs/terraform'
slug: '/guides/labs/terraform'
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';
import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<DagsterPlus />

<EarlyAccess />

[Terraform](https://developer.hashicorp.com/terraform) by HashiCorp allows you to manage your infrastructure as code. Terraform providers act as an interface between Terraform and different platforms or services in your infrastructure. The Dagster+ Terraform provider lets you programmatically manage your Dagster+ organization's resources.

The provider is open source and available through the [Terraform Registry](https://registry.terraform.io/providers/dagster-io/dagsterplus/latest/docs). You can also clone it from the [GitHub repository](https://github.com/dagster-io/terraform-provider-dagster-plus) if you want to adapt it for a custom use case or contribute improvements.

## When to use Terraform

[Terraform](https://developer.hashicorp.com/terraform) is a good fit if your organization already uses infrastructure-as-code tooling or wants to:

- **Automate onboarding** — provision deployments, invite users, and assign team permissions in a single workflow
- **Enforce consistency** — ensure configuration is identical across environments (e.g. staging and prod have the same alert policies)
- **Audit changes** — track who changed what and when through version control and Terraform state
- **Manage at scale** — coordinate many deployments, users, or secrets without manual UI work

If you only occasionally adjust settings or are just getting started with Dagster+, the UI is usually simpler.

## Getting started

### Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.0
- [A Dagster+ user token](/deployment/dagster-plus/management/tokens/user-tokens)

### Configure the provider

```hcl
terraform {
  required_providers {
    dagsterplus = {
      source  = "dagster-io/dagsterplus"
      version = "~> 0.1"
    }
  }
}

provider "dagsterplus" {
  organization = "my-org"  # subdomain of your Dagster+ URL
}
```

Set your API token as an environment variable:

```shell
export DAGSTER_CLOUD_API_TOKEN="your-api-token"
```

Initialize Terraform and apply your configuration:

```shell
terraform init
terraform apply
```

## Example

The following example creates a deployment, invites a user, and grants a team access. This is the kind of multi-step workflow that benefits most from automation:

```hcl
resource "dagsterplus_user" "alice" {
  email = "alice@example.com"
}

resource "dagsterplus_team" "data_engineering" {
  name = "data-engineering"

  deployment_grant {
    deployment = "prod"
    grant      = "EDITOR"
  }

  member {
    user_id = dagsterplus_user.alice.id
  }
}
```
