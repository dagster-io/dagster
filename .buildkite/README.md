# BuildKite Integration for Dagster

This directory contains the BuildKite pipeline configuration for testing issue-31069, which focuses on the implementation of boilerplate `definitions.py` with `@definitions` and `load_from_defs_folder`.

## Pipeline Steps

1. **Run Tests**:
   - Creates a Python virtual environment
   - Installs the project with dev dependencies
   - Runs specific tests for project commands

2. **Format Check**:
   - Runs Ruff to check formatting on the template files

3. **Manual Test Scaffolding**:
   - Scaffolds a test project
   - Verifies the generated templates contain the expected code patterns

## Setup in BuildKite

### Agent Configuration

The pipeline requires a BuildKite agent with:

- Access to the `default` queue
- GitHub authentication configured

### Environment Variables

Required secrets:

- `BUILDKITE_API_TOKEN`: For GitHub Actions integration

### Local Development

To test this pipeline locally:

1. Install the BuildKite agent
2. Set up the agent with your authentication token
3. Run the agent targeting the `default` queue
4. Push to the `issue-31069` or `install-buildkite-test-analytics` branch to trigger the pipeline

## Troubleshooting

If you encounter the "unbound variable" error with `BUILDKITE_FOLDER_GIT_REPO_PATH`, ensure the environment variables are correctly set in your agent's environment or that the post-checkout hook has been properly configured.
