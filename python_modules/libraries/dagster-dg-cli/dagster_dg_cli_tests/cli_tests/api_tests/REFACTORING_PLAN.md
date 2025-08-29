# API Test Refactoring Plan: Click Dependency Injection

## Overview
Refactor the API test infrastructure to use Click's built-in dependency injection instead of complex mocking layers. This will make tests simpler, more maintainable, and automatically support new API domains without code changes.

## Current Problems
1. **Multiple mock layers**: Currently requires 4+ layers of mocking to inject test clients
2. **Domain-specific test methods**: Each domain needs its own `_test_{domain}_command` method
3. **Hardcoded mock data**: Asset tests use hardcoded objects instead of fixture data
4. **Not extensible**: Adding new domains requires modifying test code

## Solution: Click's Dependency Injection

### Core Concept
Use Click's `obj` parameter to inject a custom context containing a GraphQL client factory. This provides a single, clean injection point for tests.

## Implementation Plan

### Phase 1: Create Context Infrastructure

#### 1.1 Create Client Factory Module
**New file: `dagster_dg_cli/utils/plus/client_factory.py`**

```python
from typing import Optional, Protocol
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient
import click


class GraphQLClientFactory(Protocol):
    """Protocol for GraphQL client factories."""
    def __call__(self, config: DagsterPlusCliConfig) -> DagsterPlusGraphQLClient:
        ...


class DgApiCliContext:
    """CLI context that holds dependencies for API commands."""
    
    def __init__(self, client_factory: Optional[GraphQLClientFactory] = None):
        self._client_factory = client_factory
    
    def create_graphql_client(self, config: DagsterPlusCliConfig) -> DagsterPlusGraphQLClient:
        """Create a GraphQL client using the configured factory."""
        if self._client_factory:
            return self._client_factory(config)
        # Default: create real client
        return DagsterPlusGraphQLClient.from_config(config)


def create_graphql_client(config: DagsterPlusCliConfig) -> DagsterPlusGraphQLClient:
    """Create GraphQL client using Click's context.
    
    This is the ONLY function that should be called to create GraphQL clients.
    It checks Click's context for a custom factory, falling back to default.
    """
    ctx = click.get_current_context()
    
    # Check if we have a custom context object
    if ctx.obj and isinstance(ctx.obj, DgApiCliContext):
        return ctx.obj.create_graphql_client(config)
    
    # Fallback to default
    return DagsterPlusGraphQLClient.from_config(config)
```

### Phase 2: Update CLI Entry Point

#### 2.1 Modify Main CLI
**File: `dagster_dg_cli/cli/__init__.py` (or main CLI location)**

```python
import click
from dagster_dg_cli.utils.plus.client_factory import DgApiCliContext

@click.group()
@click.pass_context
def cli(ctx):
    """Dagster CLI."""
    # Ensure context object exists for normal CLI usage
    ctx.ensure_object(DgApiCliContext)
```

### Phase 3: Update All GraphQL Client Creation Points

#### 3.1 Files to Update
Replace all instances of `DagsterPlusGraphQLClient.from_config(config)` with `create_graphql_client(config)`:

- `dagster_dg_cli/dagster_plus_api/graphql_adapter/deployment.py`
- `dagster_dg_cli/dagster_plus_api/graphql_adapter/asset.py`
- `dagster_dg_cli/cli/plus/create/ci_api_token.py`
- `dagster_dg_cli/cli/plus/create/env.py`
- `dagster_dg_cli/cli/plus/login.py`
- `dagster_dg_cli/cli/plus/pull/env.py`
- `dagster_dg_cli/utils/plus/build.py`
- `dagster_dg_cli/cli/list.py`
- `dagster_dg_cli/cli/scaffold/build_artifacts.py`

#### 3.2 Example Update
**Before:**
```python
def list_deployments_via_graphql(config: DagsterPlusCliConfig) -> "DeploymentList":
    client = DagsterPlusGraphQLClient.from_config(config)
    result = client.execute(LIST_DEPLOYMENTS_QUERY)
    return process_deployments_response(result)
```

**After:**
```python
from dagster_dg_cli.utils.plus.client_factory import create_graphql_client

def list_deployments_via_graphql(config: DagsterPlusCliConfig) -> "DeploymentList":
    client = create_graphql_client(config)  # Uses Click context if available
    result = client.execute(LIST_DEPLOYMENTS_QUERY)
    return process_deployments_response(result)
```

### Phase 4: Simplify Test Infrastructure

#### 4.1 New Test File Structure
**File: `dagster_dg_cli_tests/cli_tests/api_tests/test_dynamic_command_execution.py`**

```python
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from dagster_dg_cli.utils.plus.client_factory import DgApiCliContext
from dagster_dg_cli_tests.cli_tests.api_tests.shared.yaml_loader import (
    load_fixture_scenarios_from_yaml,
)


class ReplayClient:
    """GraphQL client that replays recorded responses."""
    
    def __init__(self, responses: list[dict[str, Any]]):
        self.responses = responses
        self.call_index = 0
        
    def execute(self, query: str, variables: dict = None) -> dict:
        """Return next recorded response."""
        if self.call_index >= len(self.responses):
            raise ValueError(f"Exhausted {len(self.responses)} responses")
        response = self.responses[self.call_index]
        self.call_index += 1
        return response


def discover_scenario_fixtures() -> Iterator[tuple[str, str, str]]:
    """Discover all scenario fixtures across API test domains."""
    api_tests_dir = Path(__file__).parent
    
    domain_dirs = [d for d in api_tests_dir.iterdir() if d.is_dir() and d.name.endswith("_tests")]
    
    for domain_dir in domain_dirs:
        scenarios_yaml = domain_dir / "fixtures" / "scenarios.yaml"
        if not scenarios_yaml.exists():
            continue
        
        domain = domain_dir.name.replace("_tests", "")
        fixture_scenarios = load_fixture_scenarios_from_yaml(scenarios_yaml)
        
        for fixture_name, fixture_config in fixture_scenarios.items():
            yield (domain, fixture_name, fixture_config.command)


def load_fixture_graphql_responses(domain: str, fixture_name: str) -> list[dict[str, Any]]:
    """Load GraphQL response fixtures for a given domain and fixture."""
    scenario_folder = Path(__file__).parent / f"{domain}_tests" / "fixtures" / fixture_name
    
    if not scenario_folder.exists():
        raise ValueError(f"Fixture scenario not found: {scenario_folder}")
    
    json_files = sorted([f for f in scenario_folder.glob("*.json") if f.name[0:2].isdigit()])
    
    if not json_files:
        raise ValueError(f"No numbered JSON files found in {scenario_folder}")
    
    responses = []
    for json_file in json_files:
        with open(json_file) as f:
            responses.append(json.load(f))
    
    return responses


class TestDynamicCommandExecution:
    """Test all commands from YAML fixtures against recorded GraphQL responses."""
    
    @pytest.mark.parametrize("domain,fixture_name,command", list(discover_scenario_fixtures()))
    def test_command_execution(self, domain: str, fixture_name: str, command: str, snapshot):
        """Test executing a command against its recorded GraphQL responses.
        
        Uses Click's dependency injection to provide a test client factory.
        No mocking required - just inject a context with our replay client.
        """
        from dagster_dg_cli.cli import cli as root_cli
        
        # Load GraphQL responses for this fixture
        graphql_responses = load_fixture_graphql_responses(domain, fixture_name)
        
        # Create replay client
        replay_client = ReplayClient(graphql_responses)
        
        # Create context with test factory
        test_context = DgApiCliContext(
            client_factory=lambda config: replay_client
        )
        
        # Run command with injected context - SINGLE INJECTION POINT
        runner = CliRunner()
        args = command.split()[1:]  # Skip 'dg'
        
        # Click's obj parameter passes our context through
        result = runner.invoke(root_cli, args, obj=test_context)
        
        # Snapshot testing
        output_type = "json" if "--json" in command else "text"
        snapshot_name = f"{domain}_{fixture_name}_{output_type}"
        
        if "--json" in command:
            try:
                parsed_output = json.loads(result.output)
                assert parsed_output == snapshot(name=snapshot_name)
            except json.JSONDecodeError:
                assert result.output == snapshot(name=snapshot_name)
        else:
            assert result.output == snapshot(name=snapshot_name)
        
        if "error" not in fixture_name.lower():
            assert result.exit_code == 0
```

### Phase 5: Clean Up

#### 5.1 Remove Old Code
- Delete `get_command_mapping()` function
- Delete `parse_command_string()` function  
- Delete `_test_deployment_command()` method
- Delete `_test_asset_command()` method
- Remove all hardcoded mock data

#### 5.2 Update Asset Fixtures
Ensure all asset fixtures contain real GraphQL responses instead of placeholders:
- Record actual GraphQL responses using the recording tool
- Replace placeholder JSONs with real API responses

## Benefits

### Immediate Benefits
1. **Single injection point**: Just pass `obj` to `runner.invoke()`
2. **No mocking**: Zero `mock.patch` calls needed
3. **Clean code**: ~100 lines instead of ~300
4. **Click-native**: Uses framework's intended patterns

### Long-term Benefits
1. **Future-proof**: New domains work without test changes
2. **Maintainable**: Simple, clear code structure
3. **Debuggable**: Can easily log all GraphQL calls in one place
4. **Type-safe**: Protocol ensures correct interface

## How It Works

### Normal CLI Execution
1. User runs `dg api asset list`
2. CLI creates default `DgApiCliContext` (no custom factory)
3. `create_graphql_client()` checks context, finds no custom factory
4. Falls back to `DagsterPlusGraphQLClient.from_config()`
5. Real GraphQL calls are made

### Test Execution
1. Test loads fixture responses
2. Creates `ReplayClient` with responses
3. Creates `DgApiCliContext` with lambda that returns `ReplayClient`
4. Passes context via `obj` parameter to `runner.invoke()`
5. `create_graphql_client()` checks context, finds custom factory
6. Returns `ReplayClient` instead of real client
7. Commands execute with replayed responses

## Adding New Domains

To add a new domain (e.g., "job"):

1. **Create scenarios file**: `job_tests/fixtures/scenarios.yaml`
   ```yaml
   success_list_jobs:
     command: "dg api job list --json"
   ```

2. **Record fixtures**: `dagster-dev dg-api-record job`
   Creates: `job_tests/fixtures/success_list_jobs/01_query.json`

3. **Run tests**: `pytest api_tests/job_tests/`
   Tests automatically discover and run new scenarios

**No test code changes required!**

## Migration Checklist

- [ ] Create `client_factory.py` with `DgApiCliContext`
- [ ] Update main CLI to use `ctx.ensure_object(DgApiCliContext)`
- [ ] Replace all `DagsterPlusGraphQLClient.from_config()` calls
- [ ] Update test file to use new structure
- [ ] Remove old test methods and hardcoded data
- [ ] Record real GraphQL responses for asset fixtures
- [ ] Run tests to verify everything works
- [ ] Delete old mocking code

## Success Criteria

- Tests pass with new structure
- No `mock.patch` calls in test file
- New domains can be added without modifying test code
- Test file is under 150 lines
- All fixtures use real GraphQL responses