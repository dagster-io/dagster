# Diagnose Buildkite Failure

Fast automated diagnosis of Buildkite build failures using the specialized buildkite-error-detective agent.

## Usage

```bash
/diagnose_bk_failure
```

## What it does

**Delegates to buildkite-error-detective agent** for:

- Fast parallel analysis of failing builds (30-45 second target)
- Pattern-first diagnosis of common failure types
- Specific actionable fixes with file paths and line numbers
- Distinction between functional failures vs. test infrastructure issues

**Process**:

1. **Get PR Status**: Uses `gh` CLI to fetch the current PR's status checks
2. **Find Failing Builds**: Identifies failing Buildkite builds and extracts build numbers
3. **Fetch Failure Logs**: Uses Buildkite MCP server to get detailed logs from the most recent failing build
4. **Analyze Failures**: Examines error patterns and provides diagnosis
5. **Suggest Solutions**: Recommends specific fixes or next steps

## Requirements

- **Buildkite MCP Server**: Must be configured with API tokens
  - Installation: https://github.com/buildkite/buildkite-mcp-server
  - API tokens: https://buildkite.com/user/api-access-tokens

## Example Output

**Executive Summary**: Cache Performance Regression in Asset Partition Status Methods

**Root Cause**: AssetMixin extraction broke caching behavior - `get_materialized_partitions()` called more times than expected

**Priority Fixes**:

1. **Verify AssetMixin Integration**: Check cached method delegation in asset mixin structure
2. **Cache Mechanism**: Ensure partition status queries properly cached through new mixin
3. **Method Resolution**: Confirm cache decorators preserved after method extraction

**Affected Tests**:

- `test_get_cached_partition_status_changed_time_partitions`
- `test_get_cached_partition_status_by_asset`
- Storage & GraphQL partition caching tests (8 failed jobs)

**Investigation Time**: ~35 seconds ✅
