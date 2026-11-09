---
title: 'Creating Custom Run Launchers'
description: A comprehensive guide to building custom run launchers for specialized deployment environments.
sidebar_position: 70
---

# Creating Custom Run Launchers

Run launchers are a core component of Dagster's deployment architecture, responsible for executing runs in your chosen environment. While Dagster provides built-in launchers for common platforms (Docker, Kubernetes), you may need to create a custom run launcher for specialized infrastructure or deployment requirements.

This guide provides a comprehensive walkthrough for building custom run launchers, based on community requests and production deployment patterns.

## Prerequisites

- Familiarity with Dagster's deployment architecture
- Understanding of your target execution environment (e.g., cloud services, container orchestrators)
- Python programming experience
- Knowledge of `dagster.yaml` instance configuration

## Understanding Run Launcher Architecture

### How Run Launchers Work

A run launcher bridges Dagster's orchestration layer with your execution environment. Here's the flow:

1. **Dagster Instance** calls `launch_run()` on your launcher
2. **Run Launcher** provisions resources in your target environment
3. **Run Worker** executes `dagster api execute_run` with the run configuration
4. **Run Worker** communicates back to Dagster through shared storage

### Key Components

- **Run Launcher**: Creates and manages execution environments
- **Run Worker**: The actual process that executes your Dagster code
- **Shared Storage**: How components communicate (run storage, event log, compute log)

### Communication Pattern

The run launcher and run worker communicate through Dagster's storage layer, not directly. This means:

- Both components need access to the same storage backends
- The run worker needs the same `dagster.yaml` configuration
- Network connectivity between launcher and worker is not required

## Base RunLauncher Interface

All run launchers must implement the `RunLauncher` abstract base class:

```python
import json
import time
from typing import Optional, Dict, Any

from dagster import Field, StringSource, DagsterLaunchFailedError, DagsterInvariantViolationError, execute_job, job
from dagster._config import UserConfigSchema, ConfigurableClass, ConfigurableClassData
from dagster._core.launcher.base import RunLauncher, LaunchRunContext, CheckRunHealthResult, WorkerStatus
from dagster._core.storage.dagster_run import DagsterRun

class CustomRunLauncher(RunLauncher):
    def launch_run(self, context: LaunchRunContext) -> None:
        """Launch a run in your target environment."""
        pass
    
    def terminate(self, run_id: str) -> bool:
        """Terminate a running process."""
        pass
    
    def check_run_worker_health(self, run: DagsterRun) -> CheckRunHealthResult:
        """Check if a run worker is healthy (optional)."""
        pass
```

### Required Methods

#### `launch_run(context: LaunchRunContext)`

This is the core method that:
- Receives run context including the `DagsterRun` object
- Provisions resources in your target environment
- Starts a process that executes `dagster api execute_run`
- Returns immediately (non-blocking)

#### `terminate(run_id: str) -> bool`

Terminates a running process:
- Returns `True` if successfully terminated
- Returns `False` if already terminated
- Should handle cases where the process doesn't exist

### Optional Methods

#### `check_run_worker_health(run: DagsterRun) -> CheckRunHealthResult`
Enables run monitoring by checking worker health status.

#### `get_run_worker_debug_info(run: DagsterRun) -> Optional[str]`
Returns debug information for troubleshooting failed runs.

## Step-by-Step Implementation

Let's build a custom run launcher for Azure Container Instances as an example.

### Step 1: Set Up Configuration Schema

```python
from dagster import Field, StringSource
from dagster._config import UserConfigSchema

AZURE_ACI_CONFIG_SCHEMA = {
    "resource_group": Field(StringSource, description="Azure resource group name"),
    "subscription_id": Field(StringSource, description="Azure subscription ID"),
    "image": Field(StringSource, description="Container image to use"),
    "cpu": Field(float, default_value=1.0, description="CPU allocation"),
    "memory": Field(float, default_value=1.0, description="Memory allocation in GB"),
    "environment_variables": Field(
        dict, 
        default_value={}, 
        description="Environment variables for the container"
    )
}
```

### Step 2: Implement the Launcher Class

```python
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (
    ContainerGroup, Container, ContainerGroupRestartPolicy,
    ResourceRequirements, ResourceRequests, EnvironmentVariable
)

class AzureContainerInstanceRunLauncher(RunLauncher, ConfigurableClass):
    """Launches runs in Azure Container Instances."""
    
    def __init__(
        self,
        resource_group: str,
        subscription_id: str,
        image: str,
        cpu: float = 1.0,
        memory: float = 1.0,
        environment_variables: Optional[Dict[str, str]] = None,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self.resource_group = resource_group
        self.subscription_id = subscription_id
        self.image = image
        self.cpu = cpu
        self.memory = memory
        self.environment_variables = environment_variables or {}
        self._inst_data = inst_data
        
        # Initialize Azure client
        credential = DefaultAzureCredential()
        self.client = ContainerInstanceManagementClient(
            credential, subscription_id
        )
        
        super().__init__()
    
    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return AZURE_ACI_CONFIG_SCHEMA
    
    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Dict[str, Any]
    ) -> "AzureContainerInstanceRunLauncher":
        return cls(inst_data=inst_data, **config_value)
```

### Step 3: Implement launch_run

```python
def launch_run(self, context: LaunchRunContext) -> None:
    run = context.dagster_run
    
    # Generate unique container name
    container_name = f"dagster-run-{run.run_id}"
    
    # Build the command to execute
    command = [
        "dagster",
        "api",
        "execute_run",
        "--instance-ref", self._get_instance_ref(),
        "--run-id", run.run_id,
    ]
    
    # Prepare environment variables
    env_vars = []
    for key, value in self.environment_variables.items():
        env_vars.append(EnvironmentVariable(name=key, value=value))
    
    # Create container configuration
    container = Container(
        name=container_name,
        image=self.image,
        command=command,
        resources=ResourceRequirements(
            requests=ResourceRequests(
                cpu=self.cpu,
                memory_in_gb=self.memory
            )
        ),
        environment_variables=env_vars
    )
    
    # Create container group
    container_group = ContainerGroup(
        location="East US",  # Make configurable
        containers=[container],
        os_type="Linux",
        restart_policy=ContainerGroupRestartPolicy.never,
        tags={"dagster-run-id": run.run_id}
    )
    
    try:
        # Launch the container
        self.client.container_groups.begin_create_or_update(
            self.resource_group,
            container_name,
            container_group
        )
        
        self._logger.info(f"Launched run {run.run_id} in container {container_name}")
        
    except Exception as e:
        raise DagsterLaunchFailedError(
            f"Failed to launch run {run.run_id}: {str(e)}"
        ) from e
```

### Step 4: Implement terminate

```python
def terminate(self, run_id: str) -> bool:
    container_name = f"dagster-run-{run_id}"
    
    try:
        # Check if container exists
        container_group = self.client.container_groups.get(
            self.resource_group, container_name
        )
        
        if container_group.instance_view.state in ["Terminated", "Succeeded"]:
            return False  # Already terminated
        
        # Delete the container group
        self.client.container_groups.begin_delete(
            self.resource_group, container_name
        )
        
        self._logger.info(f"Terminated container {container_name}")
        return True
        
    except Exception as e:
        self._logger.warning(f"Failed to terminate {container_name}: {e}")
        return False
```

### Step 5: Add Health Checking (Optional)

```python
@property
def supports_check_run_worker_health(self) -> bool:
    return True

def check_run_worker_health(self, run: DagsterRun) -> CheckRunHealthResult:
    container_name = f"dagster-run-{run.run_id}"
    
    try:
        container_group = self.client.container_groups.get(
            self.resource_group, container_name
        )
        
        state = container_group.instance_view.state
        
        if state == "Running":
            return CheckRunHealthResult(WorkerStatus.RUNNING)
        elif state in ["Succeeded", "Terminated"]:
            return CheckRunHealthResult(WorkerStatus.SUCCESS)
        elif state == "Failed":
            return CheckRunHealthResult(
                WorkerStatus.FAILED, 
                msg="Container failed"
            )
        else:
            return CheckRunHealthResult(WorkerStatus.UNKNOWN)
            
    except Exception as e:
        return CheckRunHealthResult(
            WorkerStatus.FAILED, 
            msg=f"Health check failed: {e}"
        )
```

## Configuration and Deployment

### dagster.yaml Configuration

```yaml
run_launcher:
  module: my_package.azure_launcher
  class: AzureContainerInstanceRunLauncher
  config:
    resource_group: "my-dagster-rg"
    subscription_id: "my-subscription-id"
    image: "my-registry/dagster-user-code:latest"
    cpu: 2.0
    memory: 4.0
    environment_variables:
      DAGSTER_POSTGRES_USER: "${DAGSTER_POSTGRES_USER}"
      DAGSTER_POSTGRES_PASSWORD: "${DAGSTER_POSTGRES_PASSWORD}"
      DAGSTER_POSTGRES_HOST: "${DAGSTER_POSTGRES_HOST}"
      DAGSTER_POSTGRES_DB: "${DAGSTER_POSTGRES_DB}"
```

### Important Configuration Notes

1. **Storage Access**: Ensure your container image can access the same storage backends
2. **Environment Variables**: Pass all necessary Dagster configuration
3. **Instance Reference**: The run worker needs to connect back to your Dagster instance
4. **Network Access**: Container must reach your Dagster storage backends

## Common Patterns and Best Practices

### Resource Management

```python
# Tag resources for cleanup
tags = {
    "dagster-run-id": run.run_id,
    "dagster-job": run.job_name,
    "created-by": "dagster",
    "created-at": str(int(time.time()))
}
```

### Error Handling

```python
try:
    # Launch logic
    pass
except ProviderSpecificError as e:
    # Handle provider-specific errors
    raise DagsterLaunchFailedError(f"Provider error: {e}") from e
except Exception as e:
    # Handle unexpected errors
    raise DagsterLaunchFailedError(f"Unexpected error: {e}") from e
```

### Logging

```python
self._logger.info(f"Launching run {run.run_id}")
self._logger.debug(f"Using image: {self.image}")
self._logger.error(f"Launch failed: {error}")
```

### Resource Cleanup

```python
def dispose(self) -> None:
    """Clean up any persistent resources."""
    # Close connections, cleanup temporary resources
    if hasattr(self, 'client'):
        self.client.close()
```

## Testing Your Run Launcher

### Unit Testing

```python
import pytest
from dagster import DagsterInstance, job
from dagster._core.test_utils import instance_for_test

def test_launch_run():
    with instance_for_test() as instance:
        launcher = AzureContainerInstanceRunLauncher(
            resource_group="test-rg",
            subscription_id="test-subscription",
            image="test-image"
        )
        
        # Create test run
        @job
        def simple_job():
            """A simple job for testing the run launcher."""
            pass
            
        run = instance.create_run_for_job(job_def=simple_job)
        
        # Test launch
        launcher.launch_run(LaunchRunContext(dagster_run=run))
        
        # Verify launch behavior
        assert launcher.can_terminate(run.run_id)
```

### Integration Testing

```python
def test_end_to_end_execution():
    # Test with actual Azure resources in a test environment
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "my_package.azure_launcher",
                "class": "AzureContainerInstanceRunLauncher",
                "config": {
                    "resource_group": "test-rg",
                    "subscription_id": "test-subscription",
                    "image": "test-image"
                }
            }
        }
    ) as instance:
        @job
        def simple_job():
            """A simple job for testing the run launcher."""
            pass
            
        result = execute_job(simple_job, instance=instance)
        assert result.success
```

## Troubleshooting

### Common Issues

#### Storage Access Problems
**Symptom**: Run worker can't connect to Dagster storage
**Solution**: Ensure network connectivity and correct environment variables

```python
# Debug storage configuration
def _validate_storage_access(self):
    """Validate that storage backends are accessible."""
    try:
        # Test database connection
        # Test object storage connection
        pass
    except Exception as e:
        raise DagsterInvariantViolationError(f"Storage validation failed: {e}")
```

#### Image and Dependency Issues
**Symptom**: Container fails to start or missing dependencies
**Solution**: Verify container image includes all required packages

```dockerfile
# Ensure your image includes Dagster and dependencies
FROM python:3.10-slim
RUN pip install dagster dagster-postgres dagster-aws
COPY requirements.txt .
RUN pip install -r requirements.txt
```

#### Authentication and Permissions
**Symptom**: Permission denied when creating resources
**Solution**: Verify credentials and IAM permissions

```python
# Test authentication during initialization
def __init__(self, ...):
    try:
        # Test authentication
        self.client.resource_groups.list()
    except Exception as e:
        raise DagsterInvariantViolationError(f"Authentication failed: {e}")
```

### Debug Information

Implement debug info collection:

```python
def get_run_worker_debug_info(self, run: DagsterRun) -> Optional[str]:
    container_name = f"dagster-run-{run.run_id}"
    
    try:
        container_group = self.client.container_groups.get(
            self.resource_group, container_name
        )
        
        debug_info = {
            "container_state": container_group.instance_view.state,
            "events": container_group.instance_view.events,
            "start_time": container_group.instance_view.start_time,
        }
        
        return json.dumps(debug_info, indent=2, default=str)
        
    except Exception as e:
        return f"Failed to get debug info: {e}"
```

## Production Considerations

### Scalability
- Consider resource limits and quotas
- Implement retry logic for transient failures
- Monitor resource usage and costs

### Security
- Use managed identities when possible
- Encrypt sensitive configuration
- Implement least-privilege access

### Monitoring
- Integrate with your monitoring stack
- Track launch success rates
- Monitor resource utilization

### Cost Optimization
- Implement resource cleanup policies
- Use appropriate instance sizes
- Consider spot/preemptible instances where applicable

## Examples and References

### Existing Implementations
Study these built-in launchers for patterns:
- [DockerRunLauncher](https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-docker/dagster_docker/docker_run_launcher.py)
- [K8sRunLauncher](https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-k8s/dagster_k8s/launcher.py)

## Community and Support

- Join the [Dagster Slack](https://dagster.slack.com) #deployment channel
- Review [deployment architecture docs](../oss-deployment-architecture.md)
- Check [GitHub issues](https://github.com/dagster-io/dagster/issues) for similar implementations

---

*This guide was created based on community feedback and production deployment experience. Please contribute improvements and examples for other cloud providers.*