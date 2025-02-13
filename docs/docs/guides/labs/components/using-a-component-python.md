---
title: "[Advanced] Adding a component to a project without yaml"
sidebar_position: 300
---


## Introduction

For some use cases, instantiating a component with Python rather than a `component.yaml` file is desirable. This guide assumes that you are already familiar with the basics of the Components system.

## Creating a subdirectory

As with yaml-based components, you'll first need to create a new subdirectory in your `components/` directory. This subdirectory will contain the component definition.

There, you'll create a `component.py` file to define your component instance. In this file, you will define a single `@component`-decorated function that instantiates the component type that you're interested in.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/python-components/component.py" language="python" />

This function just needs to return an instance of your desired component type. In our case, we've used this functionality to customize the `translator` argument of the `DbtProjectComponent` class.
