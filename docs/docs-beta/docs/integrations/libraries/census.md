---
layout: Integration
status: published
name: Census
title: Dagster & Census
sidebar_label: Census
excerpt: Trigger Census synchs from within your Dagster pipelines.
date: 2022-11-07
apireflink: http://docs.dagster.io/_apidocs/libraries/dagster-census
partnerlink: https://www.getcensus.com/
communityIntegration: true
logo: /integrations/Census.svg
categories:
  - ETL
enabledBy:
enables:
tags: [community-supported, etl]
sidebar_custom_props: 
  logo: images/integrations/census.svg
  community: true
---

With the `dagster-census` integration you can execute a Census sync and poll until that sync completes, raising an error if it's unsuccessful.

### Installation

```bash
pip install dagster-census
```

### Example

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/census.py" language="python" />

### About Census

**Census** syncs data from your cloud warehouse to the SaaS tools your organization uses. It allows everyone in your organization to take action with good data, no custom scripts or API integrations required.
