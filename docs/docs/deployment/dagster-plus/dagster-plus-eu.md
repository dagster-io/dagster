---
title: Dagster+ EU
description: TK
sidebar_position: 200
tags: [dagster-plus-feature]
---

With Dagster+ EU, your control plane, metadata, and operational data reside in European data centers. Dagster+ EU simplifies your environment, reduces compliance overhead, and speeds up round trip requests, making the UI more responsive and reducing latency when materializing assets.

EU region support is available for Hybrid and Serverless deployments of Dagster+.

## Dagster+ EU Hybrid architecture

Hybrid EU deployments are placed in the eu-north-1 region. In this architecture:

- The Dagster+ control plane runs in EU data centers.
- Your agent and compute infrastructure remain in your own environment.
- Your actual data never leaves your infrastructure. Only orchestration metadata flows to Dagster+.

## Dagster+ EU Serverless architecture

Serverless EU deployments are placed in the eu-north-1 region. In this architecture, your control plane and metadata reside in EU data centers and all your orchestration runs on managed infrastructure within the EU.
