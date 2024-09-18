---
layout: Integration
status: published
name: Meltano
title: Dagster & Meltano
sidebar_label: Meltano
excerpt: Tap into open source configurable ETL+ and the Singer integration library.
date: 2023-03-25
apireflink:
docslink: https://github.com/quantile-development/dagster-meltano#readme
partnerlink: https://meltano.com/
logo: /integrations/Meltano.svg
categories:
  - ETL
communityIntegration: true
enabledBy:
enables:
---

### About this integration

The `dagster-meltano` library allows you to run Meltano using Dagster. Design and configure ingestion jobs using the popular [Singer.io](https://singer.io) specification.

**Note** that this integration can also be [managed from the Meltano platform](https://hub.meltano.com/utilities/dagster/) using `meltano add utility dagster` and configured using `meltano config dagster set --interactive`.

### Installation

```bash
pip install dagster-meltano
```

### Example

<CodeExample filePath="integrations/meltano.py" language="python" />

### About Meltano

[Meltano](https://meltano.com/) provides data engineers with a set of tools for easily creating and managing pipelines as code by providing a wide array of composable connectors. Meltano's 'CLI for ELT+' lets you test your changes before they go live.
