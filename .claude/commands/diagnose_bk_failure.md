# Diagnose Buildkite Failure

Automatically diagnose Buildkite test failures for the current PR by fetching build information and analyzing failure logs.

## Usage

```bash
/diagnose_bk_failure
```

## What it does

1. **Get PR Status**: Uses `gh` CLI to fetch the current PR's status checks
2. **Find Failing Builds**: Identifies failing Buildkite builds and extracts build numbers
3. **Fetch Failure Logs**: Uses Buildkite MCP server to get detailed logs from the most recent failing build. 
4. **Analyze Failures**: Examines error patterns and provides diagnosis
5. **Suggest Solutions**: Recommends specific fixes or next steps

## Requirements

- **GitHub CLI (`gh`)**: Must be installed and authenticated
- **Buildkite MCP Server**: Must be installed and configured
  - Installation: https://github.com/buildkite/buildkite-mcp-server
  - API access tokens available here: https://buildkite.com/user/api-access-tokens
  - Required for fetching build logs and job details

## Output

The command will:

- List all failing Buildkite builds for the current PR
- Show detailed error messages from failed jobs
- Categorize failure types (test failures, infrastructure issues, etc.)
- Provide specific recommendations for fixing the issues
- Include direct links to failing builds for manual investigation

## Error Handling

- If not in a git repository: Shows error and exits
- If `gh` CLI is not available: Shows installation instructions
- If no PR is found: Shows error message
- If Buildkite MCP server is not configured: Shows setup instructions with manual investigation options
- If no failures are found: Confirms all builds are passing

## Example Output

```
🔍 Diagnosing Buildkite failures for current PR...
📋 Getting PR status checks...

❌ Found 1 failing Buildkite build:
   • dagster-dagster #129927

🔍 Analyzing failure logs...

📊 Failure Analysis:
   Build: dagster-dagster #129927
   Failed Jobs: 1

   Job: :pytest: automation 3.12
   Error Type: Test Failure
   Root Cause: test_check_docstrings_real_dagster_symbols[dagster.DagsterInstance] FAILED

   Details: Test expects validation output but symbol is in exclude list

💡 Recommended Fix:
   Update test in test_integration.py to handle excluded symbols

🔗 Build URL: https://buildkite.com/dagster/dagster-dagster/builds/129927
```
