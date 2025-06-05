---
description: 'Technical glossary defining key concepts: assets, definitions, partitions,
  resources, schedules, sensors, I/O managers, ops, jobs, and graphs.'
sidebar_position: 30
title: Glossary
unlisted: true
---

# Glossary

This glossary defines key Dagster concepts and terminology used throughout the documentation.

## Core Concepts

| Term | Definition |
|------|------------|
| **Asset** | A logical unit of data such as a table, dataset, or machine learning model. Assets can have dependencies on other assets, forming the data lineage for your pipelines. |
| **Asset Check** | A quality check associated with an asset to ensure it meets certain expectations around data quality, freshness or completeness. |
| **Asset Key** | A unique identifier for an asset that consists of a sequence of strings. It serves as the primary way to reference an asset throughout Dagster. |
| **Asset Materialization** | The process of computing and storing an asset's data. When an asset is materialized, Dagster executes the function that creates the asset and persists its output. |
| **Definitions** | A top-level construct that contains references to all the objects of a Dagster project, such as assets, jobs, schedules, and sensors. Only objects included in the definitions will be deployed and visible within the Dagster UI. |
| **Graph** | A structure that connects multiple ops together to form a DAG (Directed Acyclic Graph). If you are using assets, you will not need to use graphs directly. |
| **IO Manager** | Defines how data is stored and retrieved between the execution of assets and ops. This allows for customizable storage and format at any interaction in a pipeline. |
| **Job** | A subset of assets or a graph of ops that defines what should be executed together. Jobs are the main form of execution in Dagster. |
| **Op** | A computational unit of work. Ops are arranged into graphs to dictate their order of execution. Ops have largely been replaced by assets in modern Dagster usage. |
| **Resource** | A configurable external dependency such as databases, APIs, or anything outside of Dagster. Resources are defined once and can be shared across multiple assets and ops. |
| **Schedule** | A way to automate jobs or assets to occur on a specified interval. Schedules can include run configuration to parameterize execution. |
| **Sensor** | A way to trigger jobs or assets when an event occurs, such as a file being uploaded or a notification. Sensors can include run configuration for parameterized execution. |

## Deployment and Infrastructure

| Term | Definition |
|------|------------|
| **Agent** | In hybrid deployments, the agent is responsible for running user code in your environment. It polls the Dagster+ control plane for work and launches user code as appropriate. |
| **Code Location** | A collection of Definitions deployed in a specific environment. A code location determines the Python environment and can help isolate dependencies. |
| **Daemon** | A long-running process that orchestrates schedules, sensors, run queues, and run monitoring. Several Dagster features require the daemon to be running. |
| **Dagster Plus** | The managed offering of Dagster that includes a hosted Dagster instance with additional features like monitoring, alerts, and enterprise security. |
| **Executor** | An in-memory abstraction in the run worker process that manages computational resources during execution. |
| **Hybrid Deployment** | A deployment architecture where user code runs in your environment while leveraging Dagster+'s infrastructure for orchestration and metadata management. |
| **Instance** | The configuration that defines where Dagster stores the history of past runs, logs, and how to launch new runs. All processes in a Dagster deployment should share a single instance config. |
| **Run Coordinator** | Manages the queueing and prioritization of runs before they are launched by the run launcher. |
| **Run Launcher** | The interface to computational resources used to execute Dagster runs. It receives a run ID and launches the execution in the appropriate environment. |
| **Serverless** | A Dagster Plus deployment option where both the control plane and execution environment are managed by Dagster. |
| **Workspace** | The collection of code locations that make up your Dagster deployment. |

## Data Management

| Term | Definition |
|------|------------|
| **Backfill** | The process of materializing historical partitions of assets or running historical instances of jobs. |
| **Data Lineage** | The relationships and dependencies between assets that show how data flows through your pipelines. |
| **External Asset** | An asset that exists outside of Dagster's direct control but can be observed and tracked for lineage purposes. |
| **Freshness Policy** | Rules that define how recent data should be to be considered "fresh" and trigger downstream updates or alerts. |
| **Metadata** | Additional information attached to assets, runs, and other Dagster objects that provides context and observability. |
| **Multi-Asset** | A single function that produces multiple assets, useful when assets are naturally computed together. |
| **Partition** | A logical slice of a dataset or computation mapped to certain segments (such as increments of time). Partitions enable incremental processing by only running on relevant subsets of data. |

## Execution and Operations

| Term | Definition |
|------|------------|
| **Branch Deployment** | A Dagster Plus feature that allows deploying different versions of code to isolated environments for testing. |
| **Compute Logs** | The raw stdout and stderr logs from the execution of ops and asset functions. |
| **Materialization** | The act of computing and storing an asset's data by executing its associated function. |
| **Run** | An instance of executing a job or materializing assets. Each run has a unique ID and tracks the execution status and results. |
| **Run Status** | The current state of a run (e.g., queued, in progress, success, failure). |

## Automation and Scheduling

| Term | Definition |
|------|------------|
| **Asset Sensor** | A sensor that triggers based on asset materialization events. |
| **Automation Condition** | Rules that describe when an asset should be executed based on various conditions like cron schedules or dependency updates. |
| **Declarative Automation** | A framework that uses information about asset status and dependencies to automatically launch executions. |
| **Run Status Sensor** | A sensor that triggers based on the completion status of runs. |

## Configuration and Types

| Term | Definition |
|------|------------|
| **Config** | A schema applied to Dagster objects that allows for parameterization and reuse at execution time. |
| **Hook** | Functions that can be executed before or after op execution for cross-cutting concerns like monitoring or cleanup. |
| **Logger** | Configurable logging handlers that capture and route log messages from Dagster execution. |
| **Repository** | A collection of related Dagster objects like jobs, assets, and schedules (largely superseded by Definitions). |
| **Type** | A way to define and validate the data passed between ops in the type system. |

## Advanced Concepts

| Term | Definition |
|------|------------|
| **Asset Group** | A way to organize related assets together for management and execution purposes. |
| **Asset Observation** | Recording information about an asset without actually materializing it, useful for tracking external data sources. |
| **Component** | An opinionated project layout built around a Definitions object, designed to help quickly bootstrap parts of your Dagster project and serve as templates for repeatable patterns. |
| **Software-Defined Assets** | Dagster's approach where data assets are defined as code, making them version-controlled, testable, and observable. |
