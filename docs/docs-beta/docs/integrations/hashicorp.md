---
layout: Integration
status: published
name: HashiCorp Vault
title: Dagster & HashiCorp Vault
sidebar_label: HashiCorp Vault
excerpt: Centrally manage credentials and certificates, then use them in your pipelines.
date: 2022-11-07
apireflink: 
docslink: https://github.com/silentsokolov/dagster-hashicorp
partnerlink: https://www.vaultproject.io/
communityIntegration: true
logo: /integrations/Hashicorp.svg
categories:
  - Other
enabledBy:
enables:
---

### About this integration

Package for integrating HashiCorp Vault into Dagster so that you can securely manage tokens and passwords.

### Installation

```bash
pip install dagster-hashicorp
```

### Example

```python
# See the Resources docs to learn more: https://docs.dagster.io/concepts/resources

from dagster import asset, repository, with_resources
from dagster_hashicorp.vault import vault_resource
import os

@asset(required_resource_keys={"vault"})
def example_asset(context):
    secret_data = context.resources.vault.read_secret(
        secret_path="secret/data/foo/bar"
    )
    context.log.debug(f"Secret: {secret_data}")


assets = with_resources(
    [example_asset],
    {"vault": vault_resource.configured({
        "url": "vault-host:8200",
        "auth_type": {"token": {"token": os.environ['VAULT_AUTH_TOKEN']}},
    })}
)
```

### About HashiCorp Vault

**HashiCorp** provides open source tools and commercial products that enable developers, operators and security professionals to provision, secure, run and connect cloud-computing infrastructure. **HashiCorp Vault** secures, stores, and tightly controls access to tokens, passwords, certificates, API keys, and other secrets in modern computing.
