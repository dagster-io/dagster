---
title: "Run launchers"
sidebar_position: 200
---

:::note

This article applies to Dagster Open Source (OSS) deployments. For information on Dagster+, see the [Dagster+ documentation](/dagster-plus/).

:::

Runs initiated from the Dagster UI, the scheduler, or the `dagster job launch` CLI command are launched in Dagster. This is a distinct operation from executing a job using the `execute_job` Python API or the CLI `execute` command. A launch operation allocates computational resources (e.g. a process, a container, a Kubernetes pod, etc) to carry out a run execution and then instigates the execution.

The core abstraction in the launch process is the _run launcher_, which is configured as part of the [Dagster instance](/guides/deploy/dagster-instance-configuration) The run launcher is the interface to the computational resources that will be used to actually execute Dagster runs. It receives the ID of a created run and a representation of the pipeline that is about to undergo execution.

## Relevant APIs

| Name                                                              | Description                   |
| ----------------------------------------------------------------- | ----------------------------- |
| <PyObject section="internals" module="dagster._core.launcher" object="RunLauncher" /> | Base class for run launchers. |

## Built-in run launchers

The simplest run launcher is the built-in run launcher, <PyObject section="internals" module="dagster._core.launcher" object="DefaultRunLauncher" />. This run launcher spawns a new process per run on the same node as the job's code location.

Other run launchers include:

| Name | Description | Documentation |
|------|-------------|---------------|
| <PyObject section="libraries" module="dagster_k8s" object="K8sRunLauncher" /> | A run launcher that allocates a Kubernetes job per run. | [Deploying Dagster to Kubernetes](/guides/deploy/deployment-options/kubernetes/deploying-to-kubernetes) |
| <PyObject section="libraries" module="dagster_aws" object="ecs.EcsRunLauncher" /> | A run launcher that launches an Amazon ECS task per run. | [Deploying Dagster to Amazon Web Services](/guides/deploy/deployment-options/aws) |
| <PyObject section="libraries" module="dagster_docker" object="DockerRunLauncher" /> | A run launcher that launches runs in a Docker container. | [Deploying Dagster using Docker Compose](/guides/deploy/deployment-options/) |
| <PyObject section="libraries" module="dagster_celery_k8s" object="CeleryK8sRunLauncher" /> | A run launcher that launches runs as single Kubernetes jobs with extra configuration to support the `celery_k8s_job_executor`. | [Using Celery with Kubernetes](/guides/deploy/deployment-options/kubernetes/kubernetes-and-celery) |

## Custom run launchers

A few examples of when a custom run launcher is needed:

- You have custom infrastructure or custom APIs for allocating nodes for execution.
- You have custom logic for launching runs on different clusters, platforms, etc.

We refer to the process or computational resource created by the run launcher as the [run worker](/guides/deploy/oss-deployment-architecture#job-execution-flow). The run launcher only determines the behavior of the run worker. Once execution starts within the run worker, it is the executor - an in-memory abstraction in the run worker process - that takes over management of computational resources.
