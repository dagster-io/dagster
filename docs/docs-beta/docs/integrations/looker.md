---
layout: Integration
status: published
name: Looker
title: Dagster & Looker
sidebar_label: Looker
excerpt: The Looker integration allows you to monitor your Looker project as assets in Dagster, along with other data assets.
date: 2024-08-30
apireflink:
docslink: https://docs.dagster.io/_apidocs/libraries/dagster-looker
partnerlink: https://www.looker.com/
communityIntegration: true
logo: /integrations/looker.svg
categories:
  - BI
enabledBy:
enables:
---

### About this integration

Dagster allows you to represent your Looker project as assets, alongside other your other technologies like dbt and Sling. This allows you to see how your Looker assets are connected to your other data assets, and how changes to other data assets might impact your Looker project.

### Installation

```bash
pip install dagster-looker
```

### Example

<CodeExample filePath="integrations/looker.py" language="python" />

### About Looker

**Looker** is a modern platform for data analytics and visualization. It provides a unified interface for data exploration, modeling, and visualization, making it easier to understand and analyze data. Looker integrates with various data sources and can be used to create interactive reports, dashboards, and visualizations.
