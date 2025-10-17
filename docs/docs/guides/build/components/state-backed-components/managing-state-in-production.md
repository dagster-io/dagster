---
title: 'Managing state in production'
description: Learn how to refresh and manage component state in production deployments using the dg CLI.
sidebar_position: 200
---

Managing state in production depends on which state management strategy you've configured for your state-backed components. This guide explains how to refresh state for both Local Filesystem and Versioned State Storage strategies.

## Before you begin

Ensure your project is installed in the current environment where you'll run state refresh commands.

<Tabs groupId="package-manager">
<TabItem value="uv" label="uv">

```bash
uv pip install -e .
```

</TabItem>
<TabItem value="pip" label="pip">

```bash
pip install -e .
```

</TabItem>
</Tabs>

## Refreshing state for Local Filesystem deployments

If your components use the `LOCAL_FILESYSTEM` state management type, you typically refresh state during your CI/CD pipeline as part of building your Docker image.

### Basic refresh command

Run this command to refresh state for all Local Filesystem components:

```bash
dg utils refresh-defs-state --management-type LOCAL_FILESYSTEM
```

This command:
1. Discovers all state-backed components in your project
2. Filters to only those using `LOCAL_FILESYSTEM` type
3. Fetches fresh metadata from each external system (Tableau, Fivetran, etc.)
4. Writes the state to `.local_defs_state/{component_key}/state` directories
5. Reports success or failure for each component

### Example: Docker build workflow

Here's a typical GitHub Actions workflow that refreshes state during Docker image builds:

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install project
        run: |
          pip install uv
          uv pip install -e .

      - name: Refresh component state
        run: dg utils refresh-defs-state --management-type LOCAL_FILESYSTEM
        env:
          TABLEAU_CLIENT_ID: ${{ secrets.TABLEAU_CLIENT_ID }}
          TABLEAU_SECRET_ID: ${{ secrets.TABLEAU_SECRET_ID }}
          TABLEAU_SECRET_VALUE: ${{ secrets.TABLEAU_SECRET_VALUE }}
          FIVETRAN_API_KEY: ${{ secrets.FIVETRAN_API_KEY }}
          FIVETRAN_API_SECRET: ${{ secrets.FIVETRAN_API_SECRET }}

      - name: Build Docker image
        run: docker build -t my-dagster-image:latest .

      - name: Push Docker image
        run: docker push my-dagster-image:latest
```

### Dockerfile considerations

Your Dockerfile should copy the `.local_defs_state` directory into the image:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies
RUN pip install -e .

# The .local_defs_state directory is included in the COPY above
# and will be available in the container

CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-m", "my_project"]
```

Note: The `.local_defs_state` directory is automatically excluded from version control (via auto-generated `.gitignore`), but it should be included in your Docker image.

### Refreshing specific components

To refresh only specific component state keys:

```bash
dg utils refresh-defs-state \
  --management-type LOCAL_FILESYSTEM \
  --defs-state-key "TableauComponent[my_site]"
```

Or refresh multiple specific keys:

```bash
dg utils refresh-defs-state \
  --management-type LOCAL_FILESYSTEM \
  --defs-state-key "TableauComponent[my_site]" \
  --defs-state-key "FivetranAccountComponent[account_123]"
```

### When state refresh fails

If the `dg utils refresh-defs-state` command fails (for example, due to API errors or network issues), the CLI exits with a non-zero status code. This typically causes your CI/CD pipeline to fail, preventing deployment with stale or missing state.

To handle this in your deployment workflow:
- Ensure credentials are correct and have appropriate permissions
- Check that external services (Tableau, Fivetran, etc.) are accessible from your CI/CD environment
- Consider adding retry logic to your deployment scripts for transient failures
- Monitor external service status pages if failures persist

## Refreshing state for Versioned State Storage deployments

If your components use the `VERSIONED_STATE_STORAGE` state management type, the refresh workflow differs between OSS and Dagster+ deployments.

### OSS deployments

For OSS deployments, you need access to your `dagster.yaml` configuration, as the refresh command will store state in the configured instance storage.

First, ensure your `dagster.yaml` is accessible in your environment (via file path or environment variables). Then run:

```bash
dg utils refresh-defs-state --management-type VERSIONED_STATE_STORAGE
```

This command:
1. Discovers all state-backed components using `VERSIONED_STATE_STORAGE`
2. Fetches fresh metadata from each external system
3. Generates a new UUID version identifier for each state
4. Uploads state to your configured state storage backend (S3, GCS, etc.)
5. Updates the instance database with the new version identifiers

**Example: Kubernetes deployment**

For Kubernetes deployments, you might refresh state as a pre-deployment job:

```yaml
# k8s/refresh-state-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: refresh-defs-state
spec:
  template:
    spec:
      containers:
      - name: refresh-state
        image: my-dagster-image:latest
        command:
          - dg
          - utils
          - refresh-defs-state
          - --management-type
          - VERSIONED_STATE_STORAGE
        env:
          - name: DAGSTER_HOME
            value: /opt/dagster/dagster_home
        envFrom:
          - secretRef:
              name: dagster-secrets
        volumeMounts:
          - name: dagster-instance
            mountPath: /opt/dagster/dagster_home
      volumes:
        - name: dagster-instance
          configMap:
            name: dagster-instance-config
      restartPolicy: OnFailure
```

Run this job before deploying updated code locations to ensure fresh state is available.

### Dagster+ deployments

For Dagster+ deployments, use the specialized `dg plus deploy` command:

```bash
dg plus deploy refresh-defs-state
```

This command automatically:
1. Uses your Dagster+ credentials to access the cloud instance
2. Refreshes state for all `VERSIONED_STATE_STORAGE` components
3. Uploads state to Dagster+'s managed state storage
4. Updates version metadata in the Dagster+ instance

**Example: Dagster+ deployment workflow**

Integrate state refresh into your Dagster+ deployment process:

```bash
# Start deployment
dg plus deploy start

# Build and push Docker image
dg plus deploy build-and-push

# Refresh component state BEFORE finishing deployment
dg plus deploy refresh-defs-state

# Complete the deployment
dg plus deploy finish
```

This ensures that when your code location reloads, it picks up the freshest state versions.

### Refreshing specific components

Similar to Local Filesystem, you can refresh specific component keys:

```bash
# OSS
dg utils refresh-defs-state \
  --management-type VERSIONED_STATE_STORAGE \
  --defs-state-key "TableauComponent[my_site]"

# Dagster+
dg plus deploy refresh-defs-state \
  --defs-state-key "TableauComponent[my_site]"
```

### Understanding versioning

With Versioned State Storage:
- Each state refresh generates a new UUID version (e.g., `a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6`)
- Multiple versions can exist in storage simultaneously
- All runs and definitions use a consistent version until the code location reloads
- After reload, new runs use the latest version

This means you can safely update state while runs are in progress without affecting their consistency.

## Checking state status

After refreshing state, you can verify the update in the Dagster UI:

1. Navigate to the **Deployment** tab
2. Select your code location
3. View the **Defs state** section

You'll see:
- All registered defs state keys
- The last updated timestamp for each key
- The current version identifier (UUID for versioned storage, `"__local__"` for local filesystem)

## Advanced: Refreshing all state management types

To refresh state for components regardless of their management type (excluding legacy code server snapshots):

```bash
dg utils refresh-defs-state
```

Without the `--management-type` flag, this command refreshes:
- All `LOCAL_FILESYSTEM` components
- All `VERSIONED_STATE_STORAGE` components
- But skips `LEGACY_CODE_SERVER_SNAPSHOTS` components (which auto-refresh on load)

This is useful for development environments where you have a mix of state management strategies.

## Best practices

### For Local Filesystem deployments:

1. **Always refresh state during image builds** - Make `dg utils refresh-defs-state` part of your CI/CD pipeline
2. **Test state refresh in CI** - Ensure credentials and API access work in your CI environment
3. **Don't commit `.local_defs_state` to version control** - The auto-generated `.gitignore` handles this
4. **Include state directory in Docker images** - The state should be part of your deployment artifact

### For Versioned State Storage deployments:

1. **Refresh state before code location reload** - Update state, then reload to pick up new versions
2. **Monitor state storage costs** - Old versions accumulate in cloud storage; implement cleanup policies if needed
3. **Ensure instance configuration is correct** - Verify `defs_state_storage` in `dagster.yaml` points to accessible storage
4. **Use appropriate IAM permissions** - Grant read/write access to state storage for your Dagster instance

### General best practices:

1. **Handle refresh failures gracefully** - Failed refreshes should block deployments to avoid stale state
2. **Monitor external API availability** - State refresh depends on external services being accessible
3. **Consider API rate limits** - Frequent refreshes may hit rate limits for external APIs
4. **Document your state management strategy** - Make it clear which strategy your components use and why

## Next steps

- Review how to [configure state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components)
- Learn about the [Components system](/guides/build/components) in general
