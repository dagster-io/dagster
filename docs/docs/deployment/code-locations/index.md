---
description: Configure Dagster code locations and manage them with Dagster definitions.
sidebar_position: 200
title: Code locations
sidebar_class_name: hidden
canonicalUrl: '/deployment/code-locations'
slug: '/deployment/code-locations'
---

A code location is a collection of Dagster definitions loadable and accessible by Dagster's tools, such as the CLI, UI, and Dagster+. A code location comprises:

- A reference to a Python module that has an instance of <PyObject section="definitions" module="dagster" object="Definitions" /> in a top-level variable
- A Python environment that can successfully load that module

Definitions within a code location have a common namespace and must have unique names. This allows them to be grouped and organized by code location in tools.

![Code locations](/images/guides/deploy/code-locations/code-locations-diagram.png)

A single deployment can have one or multiple code locations.

Code locations are loaded in a different process and communicate with Dagster system processes over an RPC mechanism. This architecture provides several advantages:

- When there is an update to user code, the Dagster webserver/UI can pick up the change without a restart.
- You can use multiple code locations to organize jobs, but still work on all of your code locations using a single instance of the webserver/UI.
- The Dagster webserver process can run in a separate Python environment from user code so job dependencies don't need to be installed into the webserver environment.
- Each code location can be sourced from a separate Python environment, so teams can manage their dependencies (or even their Python versions) separately.