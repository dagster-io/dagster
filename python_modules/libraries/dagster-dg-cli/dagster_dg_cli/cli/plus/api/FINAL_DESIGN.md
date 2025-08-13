# Final CLI/Client Architecture Design

## Simplified Structure

```
dagster_dg_cli/
├── cli/plus/api/
│   ├── __init__.py              # Minimal - just imports
│   ├── cli_group.py             # Main API group registration
│   ├── deployment.py            # All deployment commands
│   ├── run.py                   # All run commands
│   ├── secret.py                # All secret commands
│   └── asset.py                 # All asset commands
│
└── graphql_adapter/
    ├── __init__.py
    ├── clients/
    │   ├── __init__.py
    │   ├── deployment.py
    │   ├── run.py
    │   ├── secret.py
    │   └── asset.py
    ├── models/
    │   ├── __init__.py
    │   ├── common.py
    │   ├── deployment.py
    │   ├── run.py
    │   ├── secret.py
    │   └── asset.py
    ├── queries/
    │   ├── __init__.py
    │   ├── deployment.py
    │   ├── run.py
    │   ├── secret.py
    │   └── asset.py
    └── formatters.py
```

## Implementation Examples

### CLI Layer - Main Group

```python
# cli/plus/api/cli_group.py
import click
from dagster_dg_core.utils import DgClickGroup

from .deployment import deployment_group
from .run import run_group
from .secret import secret_group
from .asset import asset_group

@click.group(
    name="api",
    cls=DgClickGroup,
    commands={
        "deployment": deployment_group,
        "run": run_group,
        "secret": secret_group,
        "asset": asset_group,
    },
)
def api_group():
    """Make REST-like API calls to Dagster Plus."""
```

### CLI Layer - Run Commands (Single File)

```python
# cli/plus/api/run.py
import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

def _get_config_or_error() -> DagsterPlusCliConfig:
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg plus` commands require authentication. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()

@click.command(name="list", cls=DgClickCommand)
@click.option("--limit", default=20, help="Maximum number of runs to return")
@click.option("--status", help="Filter by status (queued, started, success, failure)")
@click.option("--deployment", help="Filter by deployment name")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@cli_telemetry_wrapper
def list_runs_command(limit: int, status: str, deployment: str, output_json: bool):
    """List pipeline runs."""
    from dagster_dg_cli.graphql_adapter.clients.run import RunClient
    from dagster_dg_cli.graphql_adapter.formatters import format_runs

    config = _get_config_or_error()
    client = RunClient.from_config(config)

    runs = client.list_runs(
        limit=limit,
        status=status,
        deployment_name=deployment
    )

    output = format_runs(runs, as_json=output_json)
    click.echo(output)

@click.command(name="view", cls=DgClickCommand)
@click.argument("run_id")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@cli_telemetry_wrapper
def view_run_command(run_id: str, output_json: bool):
    """View details of a specific run."""
    from dagster_dg_cli.graphql_adapter.clients.run import RunClient
    from dagster_dg_cli.graphql_adapter.formatters import format_run_details

    config = _get_config_or_error()
    client = RunClient.from_config(config)

    run = client.get_run(run_id)

    output = format_run_details(run, as_json=output_json)
    click.echo(output)

@click.command(name="launch", cls=DgClickCommand)
@click.option("--pipeline", required=True, help="Pipeline name to launch")
@click.option("--deployment", help="Deployment to launch in")
@click.option("--config-file", type=click.File('r'), help="Run config JSON/YAML file")
@click.option("--tag", multiple=True, help="Tags in key=value format")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@cli_telemetry_wrapper
def launch_run_command(pipeline: str, deployment: str, config_file, tag, output_json: bool):
    """Launch a new pipeline run."""
    import json
    import yaml
    from dagster_dg_cli.graphql_adapter.clients.run import RunClient
    from dagster_dg_cli.graphql_adapter.models.run import RunLaunchRequest
    from dagster_dg_cli.graphql_adapter.formatters import format_run_details

    config = _get_config_or_error()
    client = RunClient.from_config(config)

    # Parse config file if provided
    run_config = {}
    if config_file:
        content = config_file.read()
        try:
            run_config = json.loads(content)
        except json.JSONDecodeError:
            run_config = yaml.safe_load(content)

    # Parse tags
    tags = {}
    for t in tag:
        key, value = t.split('=', 1)
        tags[key] = value

    request = RunLaunchRequest(
        pipeline_name=pipeline,
        deployment_name=deployment,
        config=run_config,
        tags=tags
    )

    run = client.launch_run(request)

    output = format_run_details(run, as_json=output_json)
    click.echo(output)

@click.command(name="terminate", cls=DgClickCommand)
@click.argument("run_id")
@click.option("--force", is_flag=True, help="Force termination without confirmation")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@cli_telemetry_wrapper
def terminate_run_command(run_id: str, force: bool, output_json: bool):
    """Terminate a running pipeline."""
    from dagster_dg_cli.graphql_adapter.clients.run import RunClient

    if not force and not output_json:
        click.confirm(f"Terminate run {run_id}?", abort=True)

    config = _get_config_or_error()
    client = RunClient.from_config(config)

    success = client.terminate_run(run_id)

    if output_json:
        click.echo(json.dumps({"success": success, "run_id": run_id}))
    else:
        click.echo(f"Successfully terminated run {run_id}")

# Group registration
@click.group(
    name="run",
    cls=DgClickGroup,
    commands={
        "list": list_runs_command,
        "view": view_run_command,
        "launch": launch_run_command,
        "terminate": terminate_run_command,
    },
)
def run_group():
    """Manage pipeline runs."""
```

### GraphQL Adapter - Models

```python
# graphql_adapter/models/run.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RunStatus(str, Enum):
    """Run status enum for FastAPI compatibility"""
    QUEUED = "QUEUED"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELED = "CANCELED"

class RunLaunchRequest(BaseModel):
    """POST /api/runs request body"""
    pipeline_name: str
    deployment_name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None

class Run(BaseModel):
    """Run resource model"""
    id: str
    pipeline_name: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    deployment_name: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)

    class Config:
        orm_mode = True  # For future ORM compatibility

class RunList(BaseModel):
    """GET /api/runs response"""
    items: List[Run]
    total: int
    has_more: bool
    cursor: Optional[str] = None
```

### GraphQL Adapter - Queries

```python
# graphql_adapter/queries/run.py
"""GraphQL queries for run operations."""

LIST_RUNS_QUERY = """
query ListRuns($limit: Int!, $cursor: String, $status: String, $deploymentName: String) {
    pipelineRunsOrError(
        limit: $limit
        cursor: $cursor
        filter: {
            statuses: [$status]
            deploymentName: $deploymentName
        }
    ) {
        ... on PipelineRuns {
            results {
                id
                pipelineName
                status
                createdTime
                updateTime
                tags {
                    key
                    value
                }
            }
            count
            cursor
        }
        ... on Error {
            message
        }
    }
}
"""

GET_RUN_QUERY = """
query GetRun($runId: String!) {
    pipelineRunOrError(runId: $runId) {
        ... on PipelineRun {
            id
            pipelineName
            status
            createdTime
            updateTime
            tags {
                key
                value
            }
        }
        ... on RunNotFoundError {
            message
        }
    }
}
"""

LAUNCH_RUN_MUTATION = """
mutation LaunchRun($executionParams: ExecutionParams!) {
    launchPipelineExecution(executionParams: $executionParams) {
        ... on LaunchRunSuccess {
            run {
                id
                pipelineName
                status
                createdTime
                updateTime
            }
        }
        ... on PipelineNotFoundError {
            message
        }
    }
}
"""

TERMINATE_RUN_MUTATION = """
mutation TerminateRun($runId: String!) {
    terminateRun(runId: $runId) {
        ... on TerminateRunSuccess {
            run {
                id
                status
            }
        }
        ... on RunNotFoundError {
            message
        }
    }
}
"""
```

### GraphQL Adapter - Client

```python
# graphql_adapter/clients/run.py
from typing import Optional
from datetime import datetime
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

from ..models.run import Run, RunList, RunLaunchRequest, RunStatus
from ..queries import run as queries

class RunClient:
    """
    REST-like client for run operations.
    Method signatures match future FastAPI endpoints.
    """

    def __init__(self, gql_client: DagsterPlusGraphQLClient):
        self.gql_client = gql_client

    @classmethod
    def from_config(cls, config: DagsterPlusCliConfig):
        """Create client from CLI config."""
        gql_client = DagsterPlusGraphQLClient.from_config(config)
        return cls(gql_client)

    def list_runs(
        self,
        limit: int = 20,
        cursor: Optional[str] = None,
        status: Optional[str] = None,
        deployment_name: Optional[str] = None,
    ) -> RunList:
        """
        GET /api/runs
        """
        result = self.gql_client.execute(
            queries.LIST_RUNS_QUERY,
            variables={
                "limit": limit,
                "cursor": cursor,
                "status": status.upper() if status else None,
                "deploymentName": deployment_name,
            }
        )

        runs_data = result["pipelineRunsOrError"]
        if runs_data.get("__typename") != "PipelineRuns":
            raise Exception(runs_data.get("message", "Unknown error"))

        runs = [
            Run(
                id=r["id"],
                pipeline_name=r["pipelineName"],
                status=RunStatus[r["status"]],
                created_at=r["createdTime"],
                updated_at=r["updateTime"],
                tags={t["key"]: t["value"] for t in r.get("tags", [])},
            )
            for r in runs_data["results"]
        ]

        return RunList(
            items=runs,
            total=runs_data["count"],
            has_more=bool(runs_data.get("cursor")),
            cursor=runs_data.get("cursor")
        )

    def get_run(self, run_id: str) -> Run:
        """
        GET /api/runs/{run_id}
        """
        result = self.gql_client.execute(
            queries.GET_RUN_QUERY,
            variables={"runId": run_id}
        )

        run_data = result["pipelineRunOrError"]
        if run_data.get("__typename") == "RunNotFoundError":
            raise ValueError(f"Run {run_id} not found")
        elif run_data.get("__typename") != "PipelineRun":
            raise Exception(run_data.get("message", "Unknown error"))

        return Run(
            id=run_data["id"],
            pipeline_name=run_data["pipelineName"],
            status=RunStatus[run_data["status"]],
            created_at=run_data["createdTime"],
            updated_at=run_data["updateTime"],
            tags={t["key"]: t["value"] for t in run_data.get("tags", [])},
        )

    def launch_run(self, request: RunLaunchRequest) -> Run:
        """
        POST /api/runs
        """
        execution_params = {
            "selector": {
                "pipelineName": request.pipeline_name,
                "repositoryLocationName": request.deployment_name or "default",
            },
            "runConfigData": request.config or {},
            "executionMetadata": {
                "tags": [
                    {"key": k, "value": v}
                    for k, v in (request.tags or {}).items()
                ]
            }
        }

        result = self.gql_client.execute(
            queries.LAUNCH_RUN_MUTATION,
            variables={"executionParams": execution_params}
        )

        launch_result = result["launchPipelineExecution"]
        if launch_result.get("__typename") != "LaunchRunSuccess":
            raise Exception(launch_result.get("message", "Failed to launch run"))

        run_data = launch_result["run"]
        return Run(
            id=run_data["id"],
            pipeline_name=run_data["pipelineName"],
            status=RunStatus[run_data["status"]],
            created_at=run_data.get("createdTime", datetime.now()),
            updated_at=run_data.get("updateTime", datetime.now()),
        )

    def terminate_run(self, run_id: str) -> bool:
        """
        DELETE /api/runs/{run_id}
        """
        result = self.gql_client.execute(
            queries.TERMINATE_RUN_MUTATION,
            variables={"runId": run_id}
        )

        terminate_result = result["terminateRun"]
        if terminate_result.get("__typename") == "RunNotFoundError":
            raise ValueError(f"Run {run_id} not found")
        elif terminate_result.get("__typename") != "TerminateRunSuccess":
            raise Exception(terminate_result.get("message", "Failed to terminate"))

        return True
```

### GraphQL Adapter - Formatters

```python
# graphql_adapter/formatters.py
"""Output formatters for CLI display."""

def format_runs(runs, as_json: bool) -> str:
    """Format run list for output."""
    if as_json:
        return runs.json(indent=2)

    lines = []
    for run in runs.items:
        lines.extend([
            f"ID: {run.id}",
            f"Pipeline: {run.pipeline_name}",
            f"Status: {run.status}",
            f"Created: {run.created_at}",
        ])
        if run.tags:
            lines.append(f"Tags: {', '.join(f'{k}={v}' for k, v in run.tags.items())}")
        lines.append("")  # Empty line between runs

    if runs.has_more:
        lines.append(f"More results available. Use --cursor {runs.cursor} to continue.")

    return "\n".join(lines)

def format_run_details(run, as_json: bool) -> str:
    """Format single run for output."""
    if as_json:
        return run.json(indent=2)

    lines = [
        f"Run ID: {run.id}",
        f"Pipeline: {run.pipeline_name}",
        f"Status: {run.status}",
        f"Created: {run.created_at}",
        f"Updated: {run.updated_at}",
    ]

    if run.deployment_name:
        lines.append(f"Deployment: {run.deployment_name}")

    if run.tags:
        lines.append("\nTags:")
        for key, value in run.tags.items():
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)

# Add more formatters as needed for other resources
```

## Benefits

1. **Simplicity**: One file per noun keeps it simple
2. **Clean separation**: CLI is just UI, business logic in adapter
3. **FastAPI-ready**: Client methods match REST patterns
4. **Easy testing**: Mock the client layer
5. **Maintainable**: Clear where each piece lives

## When to Split Files

Only split a noun file when it gets too large (>500 lines). Then use this structure:

```
cli/plus/api/
├── run/
│   ├── __init__.py        # Just imports
│   ├── cli_group.py       # Group registration
│   ├── list.py           # List command
│   ├── view.py           # View command
│   ├── launch.py         # Launch command
│   └── terminate.py      # Terminate command
```

But start simple with single files per noun.
