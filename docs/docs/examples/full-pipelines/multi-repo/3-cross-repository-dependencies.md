# Cross-Repository Dependencies

One of the most powerful features of multi-repository code locations is the ability to create asset dependencies that span across different repositories and teams. This enables organizations to maintain repository boundaries while still allowing data to flow seamlessly between teams.

## Dependency Architecture

The example demonstrates two key cross-repository dependencies:

- **ML → Analytics**: `customer_features` depends on `customer_order_summary`
- **ML → Analytics**: `product_features` depends on `product_performance`

These dependencies enable the ML team to build sophisticated features while relying on the Analytics team's data transformations, creating a natural data pipeline across organizational boundaries.

## Explicit Dependency Declaration

Cross-repository dependencies are declared explicitly using Dagster's `AssetKey` mechanism:

<CodeExample
  path="docs_projects/project_multi_repo/repo-ml/src/ml_platform/defs/models/features.py"
  language="python"
  startAfter="start_cross_repo_dependency"
  endBefore="end_cross_repo_dependency"
  title="features.py - Cross-Repository Dependency Declaration"
/>

The `deps=[AssetKey("customer_order_summary")]` declaration serves multiple purposes:

- **Lineage Tracking**: Dagster understands the dependency relationship and shows it in the asset graph
- **Execution Ordering**: Ensures upstream assets are materialized before downstream assets run
- **Impact Analysis**: Changes to upstream assets trigger appropriate downstream re-computation

The dependency is declared by asset key only - the ML repository doesn't need to know implementation details about how the Analytics team produces the data.

## Shared Storage Strategy

Cross-repository dependencies require a shared storage layer that both code locations can access:

<CodeExample
  path="docs_projects/project_multi_repo/repo-analytics/src/analytics/definitions.py"
  language="python"
  startAfter="start_shared_io_manager"
  endBefore="end_shared_io_manager"
  title="definitions.py - Shared Storage Configuration"
/>

Both repositories configure the same `FilesystemIOManager` with identical base directories. In production environments, this would typically be:

- **AWS S3**: `S3IOManager` with shared bucket access
- **Google Cloud Storage**: `GCSIOManager` with shared bucket access
- **Azure Blob Storage**: `AzureBlobStorageIOManager` with shared container access

## Manual Asset Loading Pattern

The ML repository implements a manual loading pattern for external dependencies:

<CodeExample
  path="docs_projects/project_multi_repo/repo-ml/src/ml_platform/defs/models/features.py"
  language="python"
  startAfter="start_load_external_asset"
  endBefore="end_load_external_asset"
  title="features.py - External Asset Loading Utility"
/>

This utility function provides explicit control over how external assets are loaded:

- **Error Handling**: Clear error messages when external assets aren't available
- **Path Management**: Consistent file path construction for external assets
- **Type Safety**: Returns properly typed DataFrames for downstream processing

The manual loading approach gives teams full control over error handling and data validation when consuming external dependencies.

## Asset Key Coordination

Successful cross-repository dependencies require careful coordination of asset keys between teams:

<CodeExample
  path="docs_projects/project_multi_repo/repo-analytics/src/analytics/defs/analytics_models.py"
  language="python"
  startAfter="start_customer_order_summary"
  endBefore="end_customer_order_summary"
  title="analytics_models.py - Producer Asset Definition"
/>

The Analytics team produces `customer_order_summary` with a specific asset key that the ML team references. This coordination requires:

- **Naming Conventions**: Teams must agree on asset naming patterns
- **Key Stability**: Asset keys should remain stable across deployments
- **Documentation**: Clear documentation of which assets are intended for external consumption

## Cross-Repository Execution Flow

When assets have cross-repository dependencies, execution follows a specific pattern:

1. **Analytics Materialization**: The Analytics team materializes `customer_order_summary`
2. **Storage Persistence**: The asset is persisted to shared storage via the I/O manager
3. **ML Discovery**: The ML repository's asset dependency system recognizes the available upstream asset
4. **ML Execution**: The ML team can now materialize `customer_features`, loading the upstream data

This flow enables asynchronous execution - teams can work independently while ensuring data consistency across repositories.

## Local Development and Testing

For local development, the workspace configuration enables testing cross-repository dependencies:

<CodeExample
  path="docs_projects/project_multi_repo/workspace.yaml"
  language="yaml"
  startAfter="start_workspace_config"
  endBefore="end_workspace_config"
  title="workspace.yaml - Multi-Location Development"
/>

Developers can:

1. **Start the workspace**: `DAGSTER_WORKSPACE_YAML=workspace.yaml dagster-webserver`
2. **Materialize analytics assets**: Use the UI to materialize upstream assets first
3. **Test ML dependencies**: Verify that ML assets can access analytics outputs
4. **View full lineage**: See the complete asset graph spanning both repositories

## Production Deployment Considerations

In production Dagster+ deployments, cross-repository dependencies require additional considerations:

- **Storage Permissions**: Both code locations need read/write access to shared storage
- **Network Connectivity**: Code locations must be able to access the same storage systems
- **Deployment Coordination**: Teams should coordinate deployment timing to avoid breaking dependencies
- **Monitoring**: Set up alerts for failed cross-repository asset materializations

The example's simple file-based approach translates directly to cloud storage solutions with minimal configuration changes, making it easy to evolve from local development to production deployment.

## Next steps

Now that we understand how cross-repository dependencies work technically, we can explore how to deploy and manage multiple code locations in production Dagster+ environments.

- Continue this tutorial with [Deployment Configuration](/examples/full-pipelines/multi-repo/deployment)
