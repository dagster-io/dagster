# Runs API Design - Refined Plan

## Executive Summary

This document outlines the refined design for the Runs API in Dagster Plus CLI, building on the existing API conventions while incorporating Stripe CLI-inspired patterns for handling complex nested resources.

## Core Architecture

**Follow Existing Conventions:**

- Use the established `dg plus api run <verb>` pattern from API_CONVENTIONS.md
- Implement in `/api/run.py` following the existing template structure
- Support `--json` flag for all commands per convention
- Use `DagsterPlusGraphQLClient` for all queries
- Transform GraphQL responses to REST-like JSON per established patterns

## Command Structure Overview

### Primary Commands (Standard CRUD)

```bash
# Core operations following existing patterns
dg plus api run list [--status <status>] [--pipeline <name>] [--limit <n>] [--since <date>] [--json]
dg plus api run view <run-id> [--json]                    # ✅ Already implemented
dg plus api run terminate <run-id> [--json]
dg plus api run delete <run-id> [--json]
```

### Nested Resource Access (NEW - Stripe-inspired)

```bash
# Hierarchical access to run sub-resources
dg plus api run events <run-id> [--type <event-type>] [--step <step-key>] [--limit <n>] [--json]
dg plus api run logs <run-id> [--follow] [--tail <n>] [--json]
dg plus api run stats <run-id> [--json]
dg plus api run steps <run-id> [--status <status>] [--json]
```

## Detailed Command Specifications

### 1. `dg plus api run list` (NEW)

**Purpose:** List runs with advanced filtering capabilities

**Usage:**

```bash
dg plus api run list [OPTIONS]

OPTIONS:
  --status TEXT         Filter by run status (SUCCESS|FAILURE|IN_PROGRESS|QUEUED)
  --pipeline TEXT       Filter by pipeline/job name (supports wildcards)
  --limit INTEGER       Maximum number of runs to return (default: 50)
  --since TEXT          Filter runs since date/time (ISO format or relative like "1d", "2h")
  --tags TEXT           Filter by tags (format: key=value,key2=value2)
  --latest              Show only the most recent run
  --json                Output in JSON format
```

**GraphQL Query:** `runsOrError` or `pipelineRunsOrError`

**Output Format:**

```
# Human-readable (default)
Run: 9d38c7ea-1234-5678-9abc-def012345678
Job: cloud_product_shard1_high_volume
Status: SUCCESS
Duration: 1m15s
Started: 2024-08-12 15:50:29

Run: 8c27b6d9-2345-6789-abcd-ef0123456789
Job: freshness_check_pipeline
Status: FAILURE
Duration: 0m32s
Started: 2024-08-12 15:48:15
```

### 2. `dg plus api run events` (NEW)

**Purpose:** Access run events with filtering and navigation

**Usage:**

```bash
dg plus api run events <run-id> [OPTIONS]

OPTIONS:
  --type TEXT           Event type filter (STEP_SUCCESS|STEP_FAILURE|MATERIALIZATION|etc.)
  --step TEXT           Step key filter (supports wildcards)
  --limit INTEGER       Maximum events to return (default: 100)
  --since TEXT          Events since timestamp
  --json                Output in JSON format
```

**GraphQL Query:** `logsForRun` with event filtering

**Output Format:**

```
# Human-readable table
TIMESTAMP           TYPE              STEP_KEY                    MESSAGE
2024-08-12 15:50:29 STEP_SUCCESS      cloud_product_shared1_...  Finished execution
2024-08-12 15:50:32 MATERIALIZATION   freshness_check_3aff...    Asset materialized
2024-08-12 15:50:35 STEP_SUCCESS      data_quality_check...      All checks passed
```

### 3. `dg plus api run logs` (NEW)

**Purpose:** Stream or fetch run logs with real-time capabilities

**Usage:**

```bash
dg plus api run logs <run-id> [OPTIONS]

OPTIONS:
  --follow              Follow logs in real-time (like tail -f)
  --tail INTEGER        Show last N lines (default: 100)
  --level TEXT          Log level filter (DEBUG|INFO|WARNING|ERROR)
  --step TEXT           Filter logs for specific step
  --json                Output in JSON format
```

**GraphQL Query:** `logsForRun` with cursor-based pagination

**Special Features:**

- Real-time streaming for `--follow`
- Cursor-based pagination for large log volumes
- Automatic reconnection for streaming

### 4. `dg plus api run stats` (NEW)

**Purpose:** Detailed run statistics and performance metrics

**Usage:**

```bash
dg plus api run stats <run-id> [--json]
```

**GraphQL Query:** Enhanced `runOrError` with stats field

**Output Format:**

```
# Human-readable
Run Statistics: 9d38c7ea-1234-5678-9abc-def012345678
Duration: 1m15s (75.3 seconds)
Steps: 8 succeeded, 0 failed, 0 skipped
Assets: 3 materialized, 1 observed
Checks: 12 passed, 0 failed

Timing Breakdown:
  Queue Time: 0.5s
  Start Time: 2.1s
  Execution: 72.7s
```

### 5. `dg plus api run steps` (NEW)

**Purpose:** Step-level execution details and status

**Usage:**

```bash
dg plus api run steps <run-id> [OPTIONS]

OPTIONS:
  --status TEXT         Filter by step status (succeeded|failed|skipped|in_progress)
  --pattern TEXT        Step key pattern matching
  --json                Output in JSON format
```

**GraphQL Query:** `runOrError` with `stepStats` field

**Output Format:**

```
# Human-readable table
STEP KEY                        STATUS     DURATION  ATTEMPTS
cloud_product_shared1_extract   succeeded  12.3s     1
freshness_check_3aff5132       succeeded  8.7s      1
data_quality_validation        succeeded  45.2s     1
```

### 6. `dg plus api run terminate` (NEW)

**Purpose:** Terminate running pipeline execution

**Usage:**

```bash
dg plus api run terminate <run-id> [--policy safe|immediate] [--json]
```

**GraphQL Mutation:** `terminateRun`

### 7. `dg plus api run delete` (NEW)

**Purpose:** Delete run records from the system

**Usage:**

```bash
dg plus api run delete <run-id> [--force] [--json]
```

**GraphQL Mutation:** `deletePipelineRun`

## Smart Features & Enhancements

### Context and Shortcuts

```bash
# Most recent run shortcuts
dg plus api run view --latest
dg plus api run logs --latest --follow
dg plus api run events --latest --type STEP_FAILURE

# Pipeline-specific shortcuts
dg plus api run list --pipeline "cloud_product_*" --latest
dg plus api run events $(dg plus api run list --latest --json | jq -r '.[] | .run_id') --type MATERIALIZATION
```

### Advanced Filtering

```bash
# Complex queries
dg plus api run list \
  --status SUCCESS \
  --pipeline "cloud_product_*" \
  --since "2024-08-12" \
  --tags "environment=production,freshness_check=true"

# Event-specific queries
dg plus api run events 9d38c7ea \
  --type "STEP_SUCCESS,STEP_OUTPUT" \
  --step "cloud_product_*"
```

### Output Modes

```bash
# Default: Human-readable summary
$ dg plus api run view 9d38c7ea
Run: 9d38c7ea-1234-5678-9abc-def012345678
Job: cloud_product_shard1_high_volume
Status: SUCCESS
Duration: 1m15s
Steps: 8 succeeded, 0 failed
Assets: 3 materialized

# Structured output for scripting
$ dg plus api run view 9d38c7ea --json
{
  "id": "9d38c7ea-1234-5678-9abc-def012345678",
  "run_id": "9d38c7ea",
  "status": "SUCCESS",
  "job_name": "cloud_product_shard1_high_volume",
  "duration": 75.3,
  "stats": {
    "steps_succeeded": 8,
    "steps_failed": 0,
    "materializations": 3
  }
}
```

## Implementation Plan

### Phase 1: Core Commands Extension

1. **Extend existing `run.py`** with new commands:
   - `list_runs_command()` - List runs with advanced filtering
   - `terminate_command()` - Terminate running pipeline
   - `delete_command()` - Delete run records

2. **Add helper functions:**
   - `_format_run_list_output()` - Format run list for human/JSON output
   - `_build_runs_filter()` - Convert CLI options to GraphQL filter
   - `_handle_run_mutations()` - Common pattern for terminate/delete

### Phase 2: Nested Resource Access

3. **Add nested resource commands:**
   - `logs_command()` - Access run logs via `logsForRun` GraphQL query
   - `events_command()` - Access run events with filtering
   - `stats_command()` - Detailed run statistics
   - `steps_command()` - Step-level information

4. **Advanced features:**
   - Real-time log streaming for `--follow`
   - Cursor-based pagination for large datasets
   - Smart filtering and search capabilities

### Phase 3: Polish & Integration

5. **User experience enhancements:**
   - Tab completion for run IDs, pipeline names, event types
   - Smart defaults and contextual shortcuts
   - Comprehensive error handling and user guidance

6. **Performance optimizations:**
   - Query result caching for better responsiveness
   - Efficient GraphQL query batching
   - Streaming output for large datasets

## Key Files to Modify

- **Primary:** `python_modules/libraries/dagster-dg-cli/dagster_dg_cli/cli/plus/api/run.py`
  - Extend existing `view_run_command` pattern to add 6 new command functions
  - Update `run_group` commands dictionary with new commands
  - Add shared utility functions for common patterns

- **Integration:** `python_modules/libraries/dagster-dg-cli/dagster_dg_cli/cli/plus/api/__init__.py`
  - Ensure run_group is properly registered with all new commands

## GraphQL Integration Details

### Key Queries to Use

```graphql
# For run listing
query CliRunsQuery($filter: RunsFilter, $limit: Int, $cursor: String) {
  runsOrError(filter: $filter, limit: $limit, cursor: $cursor) {
    ... on Runs {
      results {
        id
        runId
        status
        jobName
        creationTime
        startTime
        endTime
        tags {
          key
          value
        }
        stats {
          stepsSucceeded
          stepsFailed
          materializations
        }
      }
    }
  }
}

# For event access
query CliRunLogsQuery($runId: ID!, $afterCursor: String, $limit: Int) {
  logsForRun(runId: $runId, afterCursor: $afterCursor, limit: $limit) {
    ... on EventConnection {
      events {
        __typename
        ... on MessageEvent {
          runId
          message
          timestamp
          level
          stepKey
        }
      }
      cursor
      hasMore
    }
  }
}
```

### Error Handling Patterns

Following existing patterns from `run.py:114-130`:

- Handle `RunNotFoundError` cases
- Handle `PythonError` cases
- Provide consistent error formatting for JSON vs human-readable output
- Use `click.ClickException` for fatal errors

## Design Principles Applied

### 1. **Progressive Disclosure**

- Simple `run list` for basic needs
- Deep navigation (`run events`, `run logs`) for power users
- Multiple access patterns: both hierarchical and flat options

### 2. **Consistency with Existing Patterns**

- Follows established `dg plus api <noun> <verb>` structure
- Uses same GraphQL client and error handling patterns
- Maintains `--json` flag convention across all commands

### 3. **Stripe CLI Inspiration**

- Hierarchical resource access (`run events <id>` vs flat `events --run <id>`)
- Context shortcuts (`--latest` flag)
- Smart filtering and query capabilities

### 4. **Developer Experience**

- Both human-readable and machine-readable output formats
- Real-time capabilities for debugging workflows
- Comprehensive filtering for automation and scripting

This design maintains full compatibility with existing Dagster Plus CLI conventions while providing the sophisticated run management capabilities needed for complex debugging and operational workflows.
