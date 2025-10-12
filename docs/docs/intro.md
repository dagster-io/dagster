---
title: Overview
description: Dagster's Documentation
slug: /
displayed_sidebar: 'docs'
hide_table_of_contents: true
---

import {Card} from '@site/src/components/Cards';
import ThemedImage from '@theme/ThemedImage';

# Welcome to Dagster

Dagster is a data orchestrator built for data engineers, with integrated lineage, observability, a declarative programming model, and best-in-class testability.

<CodeExample
  path="docs_snippets/docs_snippets/getting-started/hello-world.py"
  language="python"
  title="defs/assets.py"
/>
<ThemedImage
  alt="Docusaurus themed image"
  style={{width: '100%', height: 'auto'}}
  sources={{
    light: './img/getting-started/lineage-light.jpg',
    dark: './img/getting-started/lineage-dark.jpg',
  }}
/>

## Get started

<div className="card-group cols-2">
  <Card
    label="Quickstart"
    href="/getting-started/quickstart"
    logo="./img/getting-started/icon-start.svg"
    description="Build your first Dagster pipeline in our Quickstart tutorial."
  />
  <Card
    label="Thinking in Assets"
    href="/guides/build/assets"
    logo="./img/getting-started/icon-assets.svg"
    description="New to Dagster? Learn about how thinking in assets can help you manage your data better."
  />
  <Card
    label="Dagster Plus"
    href="/deployment/dagster-plus"
    logo="./img/getting-started/icon-plus.svg"
    description="Learn about Dagster Plus, our managed offering that includes a hosted Dagster instance and many more features."
  />
</div>

## Join the Dagster community

<div className="card-group cols-2">
  <Card
    label="Slack"
    href="https://dagster.io/slack"
    logo="./img/getting-started/icon-slack.svg"
    description="Join our Slack community to talk with other Dagster users, use our AI-powered chatbot, and get help with Dagster."
  />
  <Card
    label="GitHub"
    href="https://github.com/dagster-io/dagster"
    logo="./img/getting-started/icon-github.svg"
    description="Star our GitHub repository and follow our development through GitHub Discussions."
  />
  <Card
    label="Youtube"
    href="https://www.youtube.com/@dagsterio"
    logo="./img/getting-started/icon-youtube.svg"
    description="Watch our latest videos on YouTube."
  />
  <Card
    label="Dagster University"
    href="https://courses.dagster.io"
    logo="./img/getting-started/icon-education.svg"
    description="Learn Dagster through interactive courses and hands-on tutorials."
  />
</div>
