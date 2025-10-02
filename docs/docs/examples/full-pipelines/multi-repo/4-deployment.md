# Deployment Configuration

Deploying multi-repository code locations in Dagster+ requires careful configuration of each repository's deployment settings and coordination between teams. This page covers the deployment patterns and best practices for managing multiple code locations in production.

## Individual Repository Configuration

Each repository maintains its own Dagster+ deployment configuration in the `dagster_cloud.yaml` file:

<CodeExample
  path="docs_projects/project_multi_repo/repo-analytics/dagster_cloud.yaml"
  language="yaml"
  startAfter="start_analytics_cloud_config"
  endBefore="end_analytics_cloud_config"
  title="repo-analytics/dagster_cloud.yaml"
/>

The Analytics repository configuration demonstrates key deployment settings:

- **Location Name**: `analytics-team` provides a unique identifier in the Dagster+ workspace
- **Code Source**: Points to the specific Python module containing the definitions
- **Build Directory**: Specifies the root directory for building the deployment package

The configuration includes optional sections for custom Docker registries, compute resources, and environment variables that teams can customize based on their specific requirements.

## ML Repository Deployment

The ML repository has similar configuration with ML-specific optimizations:

<CodeExample
  path="docs_projects/project_multi_repo/repo-ml/dagster_cloud.yaml"
  language="yaml"
  startAfter="start_ml_cloud_config"
  endBefore="end_ml_cloud_config"
  title="repo-ml/dagster_cloud.yaml"
/>

The ML configuration shows considerations for compute-intensive workloads:

- **Custom Resource Allocation**: Comments show how to specify higher CPU and memory for ML workloads
- **ML-Specific Environment Variables**: Placeholder for model registry URLs and ML tracking systems
- **Separate Registry**: Option to use different Docker registries optimized for ML dependencies

These configurations enable each team to optimize their deployment for their specific workload characteristics.

## Branch Deployment Strategy

Multi-repository setups support flexible branch deployment strategies where each repository can have independent deployment workflows:

### Analytics Team Workflow

```yaml
# Example branch deployment for analytics
locations:
  - location_name: analytics-team-dev
    code_source:
      python_file: analytics/definitions.py
    build:
      directory: .
      registry: your-registry.amazonaws.com/analytics-dev
```

### ML Team Workflow

```yaml
# Example branch deployment for ML
locations:
  - location_name: ml-platform-dev
    code_source:
      python_file: ml_platform/definitions.py
    build:
      directory: .
      registry: your-registry.amazonaws.com/ml-dev
```

This pattern allows teams to:

- **Independent Development**: Test changes without affecting other teams
- **Parallel Feature Development**: Work on different features simultaneously
- **Staged Rollouts**: Deploy to development, staging, and production independently

## Production Deployment Coordination

While repositories can deploy independently, production deployments require coordination to maintain cross-repository dependencies:

### Deployment Sequence Considerations

1. **Analytics First**: Deploy analytics changes before ML dependencies
2. **Backward Compatibility**: Ensure upstream changes don't break downstream consumers
3. **Coordinated Rollbacks**: Plan rollback strategies that consider cross-repository dependencies

### Shared Resource Management

Production deployments must coordinate shared resources:

<CodeExample
  path="docs_projects/project_multi_repo/repo-analytics/src/analytics/definitions.py"
  language="python"
  startAfter="start_shared_io_manager"
  endBefore="end_shared_io_manager"
  title="Production Resource Configuration"
/>

In production, teams replace the `FilesystemIOManager` with cloud storage:

```python
# Production S3 configuration
resources={
    "io_manager": S3IOManager(
        s3_bucket="your-dagster-assets",
        s3_prefix="multi-repo-assets"
    )
}
```

Both repositories must use identical storage configurations to maintain cross-repository asset access.

## Environment-Specific Configuration

Teams can customize deployments for different environments using environment variables and configuration templating:

### Development Environment

```yaml
locations:
  - location_name: analytics-team
    code_source:
      python_file: analytics/definitions.py
    env_vars:
      - ENVIRONMENT=development
      - STORAGE_BUCKET=dagster-dev-assets
      - LOG_LEVEL=DEBUG
```

### Production Environment

```yaml
locations:
  - location_name: analytics-team
    code_source:
      python_file: analytics/definitions.py
    env_vars:
      - ENVIRONMENT=production
      - STORAGE_BUCKET=dagster-prod-assets
      - LOG_LEVEL=INFO
```

This approach enables teams to maintain environment-specific configurations while using the same codebase across development, staging, and production.

## Monitoring and Observability

Multi-repository deployments require enhanced monitoring to track cross-repository dependencies:

### Asset Lineage Tracking

- Monitor asset materialization success rates across code locations
- Set up alerts for failed cross-repository dependencies
- Track data freshness for assets consumed by multiple teams

### Performance Monitoring

- Monitor compute resource utilization for each code location
- Track execution times for cross-repository asset pipelines
- Set up capacity planning for shared storage systems

### Team-Specific Dashboards

- Create dashboards showing each team's asset health
- Display cross-repository dependency status
- Monitor deployment success rates per repository

## Best Practices for Multi-Repository Deployments

1. **Naming Conventions**: Use consistent naming patterns for code locations and assets
2. **Dependency Documentation**: Maintain clear documentation of cross-repository dependencies
3. **Deployment Testing**: Test deployments in staging environments that mirror production
4. **Rollback Planning**: Develop rollback procedures that consider cross-repository impacts
5. **Resource Isolation**: Use separate compute resources for different teams when appropriate
6. **Security Boundaries**: Implement appropriate access controls for shared storage and resources

The multi-repository pattern provides organizational flexibility while maintaining technical integration, enabling teams to work independently while building cohesive data platforms.
