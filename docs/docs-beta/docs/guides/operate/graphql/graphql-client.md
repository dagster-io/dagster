---
title: "Dagster GraphQL Python client"
description: Dagster provides a Python client to interact with its GraphQL API
---

Dagster provides a GraphQL Python Client to interface with [Dagster's GraphQL API](index.md) from Python.

## Relevant APIs

| Name                                                                    | Description                                                          |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------- |
| <PyObject section="libraries" module="dagster_graphql" object="DagsterGraphQLClient"/>      | The client class to interact with Dagster's GraphQL API from Python. |
| <PyObject section="libraries" module="dagster_graphql" object="DagsterGraphQLClientError"/> | The exception that the client raises upon a response error.          |

## Overview

The Dagster Python Client provides bindings in Python to programmatically interact with Dagster's GraphQL API.

When is this useful? Dagster exposes a powerful GraphQL API, but this level of flexibility is not always necessary. For example, when submitting a new job run, you may only want to think about the job name and configuration and to think less about maintaining a long GraphQL query.

`DagsterGraphQLClient` provides a way to solve this issue by providing a module with a simple interface to interact with the GraphQL API.

Note that all GraphQL methods on the API are not yet available in Python - the `DagsterGraphQLClient` currently only provides the following methods:

- <PyObject
  section="libraries"
  module="dagster_graphql"
  object="DagsterGraphQLClient"
  method="submit_job_execution"
  />
- <PyObject
  section="libraries"
  module="dagster_graphql"
  object="DagsterGraphQLClient"
  method="get_run_status"
  />
- <PyObject
  section="libraries"
  module="dagster_graphql"
  object="DagsterGraphQLClient"
  method="reload_repository_location"
  />
- <PyObject
  section="libraries"
  module="dagster_graphql"
  object="DagsterGraphQLClient"
  method="shutdown_repository_location"
  />

## Using the GraphQL Client

The snippet below shows example instantiation of the client:

<CodeExample path="docs_snippets/docs_snippets/concepts/webserver/graphql/client_example.py" startAfter="start_setup_marker" endBefore="end_setup_marker" />

If you are using Dagster+, you can configure your client against the Dagster+ API by passing your deployment-specific URL and a User Token to the client as follows:

<CodeExample path="docs_snippets/docs_snippets/concepts/webserver/graphql/client_example.py" startAfter="start_cloud_usage" endBefore="end_cloud_usage" />

## Examples

### Getting a job run's status

You can use the client to get the status of a job run as follows:

<CodeExample path="docs_snippets/docs_snippets/concepts/webserver/graphql/client_example.py" startAfter="start_run_status_marker" endBefore="end_run_status_marker" />

### Reloading all repositories in a repository location

You can also reload a repository location in a Dagster deployment.

This reloads all repositories in that repository location. This is useful in a variety of contexts, including refreshing the Dagster UI without restarting the server. Example usage is as follows:

<CodeExample path="docs_snippets/docs_snippets/concepts/webserver/graphql/client_example.py" startAfter="start_reload_repo_location_marker" endBefore="end_reload_repo_location_marker" />

### Submitting a job run

You can use the client to submit a job run as follows:

<CodeExample path="docs_snippets/docs_snippets/concepts/webserver/graphql/client_example.py" startAfter="start_submit_marker_default" endBefore="end_submit_marker_default" />

### Shutting down a repository location server

If you're running your own gRPC server, we generally recommend updating your repository code by building a new Docker image with a new tag and redeploying your server using that new image, but sometimes you may want to restart your server without changing the image (for example, if your job definitions are generated programatically from a database, and you want to restart the server and re-generate your repositories even though the underlying Python code hasn't changed). In these situations, `reload_repository_location` is insufficient, since it refreshes the UI's information about the repositories but doesn't actually restart the server or reload the repository definition.

One way to cause your server to restart and your repositories to be reloaded is to run your server in an environment like Kubernetes that automatically restarts services when they fail (or docker-compose with `restart: always` set on the service), and then use the `shutdown_repository_location` function on the GraphQL client to shut down the server. The server will then be restarted by your environment, which will be automatically detected by the UI.

Example usage:


<CodeExample path="docs_snippets/docs_snippets/concepts/webserver/graphql/client_example.py" startAfter="start_shutdown_repo_location_marker" endBefore="end_shutdown_repo_location_marker" />

#### Repository location and repository inference

Note that specifying the repository location name and repository name are not always necessary; the GraphQL client will infer the repository name and repository location name if the job name is unique.

<CodeExample path="docs_snippets/docs_snippets/concepts/webserver/graphql/client_example.py" startAfter="start_submit_marker_job_name_only" endBefore="end_submit_marker_job_name_only" />
