---
title: 'Testing component definitions'
sidebar_position: 700
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

Once you have scaffolded components into your `defs` folder you want to be able to test. We provide testing utilities for doing so.

Imagine we have created a very simple component:


<CodeExample
  path="docs_snippets/docs_snippets/guides/components/testing-component-defs/1-simple-component.py"
  language="python"
  title="my_project/src/my_project/lib/simple_component.py"
/>

And we have an instance of it:

