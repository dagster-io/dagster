---
title: Overview
description: Dagster's Documentation
slug: /
displayed_sidebar: 'docs'
hide_table_of_contents: true
---

import { Card, CardGroup } from '@site/src/components/Cards';
import ThemedImage from '@theme/ThemedImage';

# Welcome to Dagster

Dagster is a data orchestrator built for data engineers, with integrated lineage, observability, a declarative programming model and best-in-class testability.

<CodeExample filePath="getting-started/hello-world.py" language="python" />
<ThemedImage
  alt="Docusaurus themed image"
  style={{width:'100%', height: 'auto'}}
  sources={{
    light: './img/getting-started/lineage-light.jpg',
    dark: './img/getting-started/lineage-dark.jpg',
  }}
/>

## Get started

<CardGroup cols={3}>
  <Card title="Quickstart" href="/getting-started/quickstart" imagePath="./img/getting-started/icon-start.svg">
      Build your first Dagster pipeline in our Quickstart tutorial.
  </Card>
  <Card title="Thinking in Assets"  href="/concepts/assets/thinking-in-assets" imagePath="./img/getting-started/icon-assets.svg">
    New to Dagster? Learn about how thinking in assets can help you manage your data better.
  </Card>
  <Card title="Dagster Plus" href="/dagster-plus/whats-dagster-plus" imagePath="./img/getting-started/icon-plus.svg">
    Learn about Dagster Plus, our managed offering that includes a hosted Dagster instance and many more features.
  </Card>
</CardGroup>

## Join the Dagster community

<CardGroup cols={3}>
  <Card title="Slack" href="https://dagster.io/slack" imagePath="./img/getting-started/icon-slack.svg">
    Join our Slack community to talk with other Dagster users, use our AI-powered chatbot, and get help with Dagster.
  </Card>
  <Card title="GitHub" href="https://github.com/dagster-io/dagster" imagePath="./img/getting-started/icon-github.svg">
    Star our GitHub repository and follow our development through GitHub Discussions.
  </Card>
  <Card title="Youtube" href="https://www.youtube.com/@dagsterio" imagePath="./img/getting-started/icon-youtube.svg">
    Watch our latest videos on YouTube.
  </Card>
</CardGroup>
