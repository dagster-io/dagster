---
title: Dagster & HashiCorp Vault
sidebar_label: HashiCorp Vault
description: Centrally manage credentials and certificates, then use them in your pipelines.
tags:
source: https://github.com/silentsokolov/dagster-hashicorp
pypi: https://pypi.org/project/dagster-hashicorp/
built_by: Community
keywords:
unlisted: false
sidebar_custom_props:
  logo: images/integrations/hashicorp.svg
  community: true
partnerlink: https://www.vaultproject.io/
---

Package for integrating HashiCorp Vault into Dagster so that you can securely manage tokens and passwords.

### Installation

```bash
pip install dagster-hashicorp
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/hashicorp.py" language="python" />

### About HashiCorp Vault

**HashiCorp** provides open source tools and commercial products that enable developers, operators and security professionals to provision, secure, run and connect cloud-computing infrastructure. **HashiCorp Vault** secures, stores, and tightly controls access to tokens, passwords, certificates, API keys, and other secrets in modern computing.
