---
title: Multi-Repository Code Locations
description: Learn how to set up multiple code locations in Dagster+ with cross-repository asset dependencies
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/multi-repo'
slug: '/examples/full-pipelines/multi-repo'
---

# Multi-Repository Code Locations

In this tutorial, you'll build a multi-repository data platform with Dagster+ that:

- Separates Analytics and ML teams into independent repositories
- Enables cross-repository asset dependencies and data sharing
- Implements shared resource configurations for seamless data flow
- Demonstrates independent deployment cycles for different teams
- Shows how to coordinate production deployments across repositories

You will learn to:

- Set up multiple code locations with independent repositories
- Configure shared storage for cross-repository asset access
- Declare and manage cross-repository asset dependencies
- Organize teams with different development and deployment schedules
- Deploy multiple code locations to Dagster+ with proper coordination
- Monitor and maintain cross-repository data pipelines

## Prerequisites

To follow the steps in this tutorial, you'll need:

- Python 3.9+ installed. For more information, see the [Installation guide](/getting-started/installation).
- A [Dagster+ account](https://dagster.cloud/signup) for deployment examples.
- Familiarity with Python, data pipelines, and basic machine learning concepts.
- Understanding of Git workflows and repository management.

## Architecture Overview

This example demonstrates a realistic multi-team scenario with two separate repositories:

- **Analytics Team Repository** (`repo-analytics/`): Handles data ingestion, transformation, and business reporting
- **ML Platform Team Repository** (`repo-ml/`): Manages feature engineering, model training, and predictions

Despite being in separate repositories, assets in one code location can depend on assets from another code location, enabling cross-team collaboration while maintaining clear organizational boundaries.

## Multi-Repository Structure

Each repository is structured as an independent Dagster project with its own configuration:

<CodeExample
  path="docs_projects/project_multi_repo/workspace.yaml"
  language="yaml"
  startAfter="start_workspace_config"
  endBefore="end_workspace_config"
  title="workspace.yaml"
/>

The workspace configuration defines two separate code locations, each pointing to a different Python package and working directory. This allows both repositories to be loaded simultaneously in a single Dagster instance while maintaining clear separation.

## Cross-Repository Dependencies

The example demonstrates how assets in the ML repository can depend on assets from the Analytics repository:

- `customer_features` depends on `customer_order_summary` (from analytics)
- `product_features` depends on `product_performance` (from analytics)

These dependencies are handled through explicit asset key references and shared storage, enabling cross-team data collaboration while maintaining repository independence.

## Shared Resource Configuration

Both repositories use a shared I/O manager configuration to enable cross-repository asset dependencies:

<CodeExample
  path="docs_projects/project_multi_repo/repo-analytics/src/analytics/definitions.py"
  language="python"
  startAfter="start_shared_io_manager"
  endBefore="end_shared_io_manager"
  title="repo-analytics/src/analytics/definitions.py"
/>

The `FilesystemIOManager` with a shared base directory ensures that assets materialized in one repository can be accessed by assets in another repository. In production, this would typically be replaced with cloud storage like S3 or GCS.

## Next steps

- Continue this tutorial with [Analytics Repository](/examples/full-pipelines/multi-repo/analytics-repository)
