---
layout: Integration
status: published
name: Hightouch
title: Dagster & Hightouch
sidebar_label: Hightouch
excerpt: Trigger syncs and monitor them until they complete.
date: 2022-11-07
docslink: https://github.com/hightouchio/dagster-hightouch
partnerlink: https://hightouch.com/
communityIntegration: true
logo: /integrations/Hightouch.svg
categories:
  - ETL
enabledBy:
enables:
---

### About this integration

With this integration you can trigger Hightouch syncs and monitor them from within Dagster. Fine-tune when Hightouch syncs kick-off, visualize their dependencies, and monitor the steps in your data activation workflow.

This native integration helps your team more effectively orchestrate the last mile of data analytics—bringing that data from the warehouse back into the SaaS tools your business teams live in. With the `dagster-hightouch` integration, Hightouch users have more granular and sophisticated control over when data gets activated.

### Installation

```bash
pip install dagster-hightouch
```

### Example

<CodeExample filePath="integrations/hightouch.py" language="python" />

### About Hightouch

**Hightouch** syncs data from any data warehouse into popular SaaS tools that businesses run on. Hightouch uses the power of Reverse ETL to transform core business applications from isolated data islands into powerful integrated solutions.
