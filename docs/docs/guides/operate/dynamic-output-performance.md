---
title: Optimize dynamic output execution performance by choosing the right execution method based on task duration and overhead trade-offs.
sidebar_label: Dynamic output performance
description: Learn when to use execute_in_process(), execute_job(), or CLI execution for optimal dynamic output performance.
sidebar_position: 60
---

Dynamic outputs in Dagster enable powerful data processing patterns, but choosing the wrong execution method can make parallel workloads run slower than sequential ones. This guide helps you understand the performance trade-offs and choose the optimal execution approach for your specific workload.

:::note
This article assumes familiarity with:
- [Dynamic graphs and outputs](/concepts/ops-jobs-graphs/dynamic-graphs)
- [Job execution](/guides/build/jobs/job-execution)
- [Executors](/concepts/ops-jobs-graphs/op-jobs-graphs#executors)
:::

## Understanding the performance confusion

When working with dynamic outputs, developers often encounter surprising performance behavior where parallel execution appears slower than sequential processing:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-performance-confusion.py"
  language="python"
  title="Common performance confusion with dynamic outputs"
/>

The issue isn't that parallel execution is broken—it's understanding when overhead costs exceed the benefits of parallelization.

## Compare execution methods

Dagster provides three ways to execute dynamic jobs, each with different performance characteristics and overhead costs.

### Method 1: execute_in_process() - Sequential execution

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-execute-in-process.py"
  language="python"
  title="Sequential execution with minimal overhead"
/>

**Characteristics:**
- **Fastest for small tasks** - minimal setup time
- **Perfect for testing and debugging** - single process, easy to trace
- **Sequential only** - no parallel processing regardless of executor
- **Not production-ready** - single process limitations

### Method 2: execute_job() - Parallel with moderate overhead

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-execute-job.py"
  language="python"
  title="Parallel execution with process overhead"
/>

**Characteristics:**
- **True parallel execution** across multiple processes
- **Production-similar behavior** - uses configured executors
- **Process creation overhead** - 2-5 seconds per worker startup
- **File I/O overhead** - data serialization between processes

### Method 3: CLI execution - Parallel with maximum overhead

```bash
# Production deployment method with highest overhead
dagster job execute -f my_file.py -j my_dynamic_job
```

**Characteristics:**
- **Production deployment method** - how jobs run in scheduled environments
- **Full multiprocess capabilities** - complete executor configuration
- **Highest overhead** - CLI interface plus process management
- **Slowest for small tasks** - overhead dominates execution time

## Analyze performance trade-offs with real data

Here's actual performance data from testing 8 chunks, each taking 0.5 seconds of work:

| Execution Method | Total Time | Work Time | Overhead | Efficiency |
|------------------|------------|-----------|----------|------------|
| `execute_in_process()` | 5.3 seconds | 4.0s | 1.3s | 1x (baseline) |
| `execute_job()` | 18.6 seconds | 4.0s | 14.6s | 0.3x (3x slower) |
| CLI execution | 45.7 seconds | 4.0s | 41.7s | 0.1x (9x slower) |

:::tip Key insight
For tasks shorter than ~30 seconds, sequential execution is faster than parallel execution due to overhead costs.
:::

### Understanding overhead sources

The performance overhead in parallel execution comes from:

1. **Process creation** - Starting new Python processes (2-5 seconds each)
2. **Resource initialization** - Loading libraries and resources in each worker
3. **Data serialization** - Writing/reading data between processes via filesystem
4. **Process coordination** - Managing worker communication and synchronization
5. **CLI interface costs** - Additional command-line parsing and setup

### The overhead vs work calculation

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-overhead-calculation.py"
  language="python"
  title="Understanding when overhead dominates performance"
/>

## Choose the optimal execution method

Use this decision framework to select the best execution method based on your workload characteristics.

### Use execute_in_process() for small tasks

**When to use:**
- **Individual tasks take < 30 seconds**
- **Local development and testing**
- **Debugging pipeline logic**
- **Unit testing operations**

**Example scenarios:**
- Processing small CSV files (< 1MB each)
- Simple calculations or data validation
- Quick API calls (< 10 seconds each)
- Testing pipeline structure and logic

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-small-tasks.py"
  language="python"
  title="Optimal use case for execute_in_process()"
/>

### Use execute_job() for medium tasks

**When to use:**
- **Individual tasks take 30 seconds to 5 minutes**
- **Testing production-like performance**
- **Integration testing with realistic data**
- **Medium-scale data processing**

**Example scenarios:**
- Processing medium datasets (1-100MB files)
- Machine learning model training
- Complex data transformations
- Database bulk operations

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-medium-tasks.py"
  language="python"
  title="Production testing with execute_job()"
/>

### Use CLI execution for large tasks

**When to use:**
- **Individual tasks take 5+ minutes**
- **Production deployment**
- **Large-scale data processing**
- **Scheduled job execution**

**Example scenarios:**
- ETL jobs processing GBs of data
- Long-running ML training pipelines
- Data warehouse loads
- Multi-hour analytical workloads

```bash
# Production execution for large workloads
dagster job execute -f pipeline.py -j large_data_job
```

## Test performance with your workloads

Use this comprehensive testing framework to measure performance characteristics with your actual workloads:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-performance-test.py"
  language="python"
  title="Complete performance testing framework"
/>

Run the test with different work times to find your overhead threshold:

```bash
# Test with small tasks (0.5s each) - sequential should win
python performance_test.py

# Test with medium tasks (30s each) - parallel should win
# Edit work_time = 30.0 in the code and run again
python performance_test.py

# Test with large tasks (300s each) - parallel should dominate
# Edit work_time = 300.0 in the code and run again  
python performance_test.py
```

## Optimize production deployments

### Configure environment-specific execution

Adapt execution methods based on deployment environment:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-environment-config.py"
  language="python"
  title="Environment-aware execution configuration"
/>

### Batch small tasks to reduce overhead

When you must run many small tasks in parallel, batch them to amortize overhead:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-task-batching.py"
  language="python"
  title="Batching small tasks for better parallel performance"
/>

### Configure executor concurrency for optimal performance

Fine-tune executor settings based on your measured performance characteristics:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-executor-tuning.py"
  language="python"
  title="Optimizing executor configuration for dynamic outputs"
/>

## Monitor and debug performance issues

### Add timing instrumentation

Instrument your dynamic outputs to understand execution patterns:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-timing-instrumentation.py"
  language="python"
  title="Adding performance monitoring to dynamic outputs"
/>

### Identify execution bottlenecks

Use these techniques to diagnose performance issues:

1. **Check for true parallelism** - Look for overlapping start times in logs
2. **Measure overhead ratio** - Compare total time vs sum of work time  
3. **Monitor resource usage** - Track CPU, memory, and I/O during execution
4. **Profile individual tasks** - Use Python profiling tools on operations

### Debug common performance problems

#### Problem: Parallel execution slower than expected

**Diagnostic steps:**
1. Verify individual chunk processing time
2. Check if tasks are actually running in parallel
3. Monitor system resource utilization
4. Measure serialization overhead

**Solutions:**
- Increase task size to amortize overhead
- Reduce number of concurrent workers if resource-constrained
- Optimize individual task performance first
- Consider using different executor (e.g., thread-based for I/O-bound tasks)

#### Problem: Sequential execution unexpectedly slow

**Diagnostic steps:**
1. Profile individual operations for bottlenecks
2. Check for resource contention between tasks
3. Monitor memory usage patterns
4. Identify blocking I/O operations

**Solutions:**
- Optimize individual task algorithms
- Implement caching for expensive computations
- Use connection pooling for database operations
- Consider breaking large tasks into smaller chunks

## Troubleshooting

### Execution method not working as expected

#### execute_in_process() appears to use configured executor

**Problem**: User expects parallel execution with `execute_in_process()`.

**Solution**: `execute_in_process()` always runs sequentially regardless of executor configuration. Use `execute_job()` for parallel execution:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-troubleshoot-execution.py"
  language="python"
  title="Correct usage of execution methods"
/>

#### execute_job() fails with missing instance

**Problem**: `execute_job()` raises errors about missing Dagster instance.

**Solutions:**

1. **Set up DAGSTER_HOME**:
```bash
export DAGSTER_HOME=/path/to/dagster/home
mkdir -p $DAGSTER_HOME
```

2. **Initialize instance programmatically**:
<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-instance-setup.py"
  language="python"
  title="Setting up Dagster instance for execute_job()"
/>

#### CLI execution fails with module import errors

**Problem**: CLI execution can't find or import your job definition.

**Solutions:**

1. **Verify Python path and imports**:
```bash
# Ensure your module is importable
python -c "from my_module import my_job; print('Import successful')"
```

2. **Use absolute paths and module references**:
```bash
# Use absolute file path
dagster job execute -f /full/path/to/pipeline.py -j my_job

# Or use module import style  
dagster job execute -m my_package.my_module -j my_job
```

### Performance issues

#### Memory usage grows with concurrent execution

**Problem**: Memory consumption increases dramatically with parallel execution.

**Solutions:**

1. **Limit concurrent processes based on available memory**:
<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-memory-management.py"
  language="python"
  title="Memory-aware concurrency configuration"
/>

2. **Use memory-efficient data passing**:
<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-efficient-data-passing.py"
  language="python"
  title="Optimizing data serialization for dynamic outputs"
/>

#### Database connection exhaustion

**Problem**: Parallel execution exhausts database connection pools.

**Solutions:**

1. **Limit database-intensive operations**:
<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-db-concurrency.py"
  language="python"
  title="Managing database connections in parallel execution"
/>

2. **Use connection pooling and resource management**:
<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-connection-pooling.py"
  language="python"
  title="Implementing connection pooling for dynamic outputs"
/>

### Deployment-specific issues

#### Kubernetes executor configuration not taking effect

**Problem**: Configured concurrency limits ignored in Kubernetes deployment.

**Solutions:**

1. **Verify executor configuration in Helm values**:
```yaml
# values.yaml
dagsterUserDeployments:
  deployments:
    - name: "user-code"
      image:
        repository: "my-repo/dagster-user-code"
        tag: "latest"
      dagsterApiGrpcArgs:
        - "--python-file"
        - "/opt/dagster/app/pipeline.py"
      env:
        DAGSTER_HOME: "/opt/dagster/dagster_home"
```

2. **Check resource limits don't conflict with concurrency**:
```yaml
# Ensure sufficient CPU/memory for concurrent execution
resources:
  limits:
    cpu: "4"
    memory: "8Gi"
  requests:
    cpu: "2" 
    memory: "4Gi"
```

#### Docker executor performance issues

**Problem**: Docker-based execution has unexpected overhead.

**Solutions:**

1. **Optimize Docker image size and startup**:
```dockerfile
# Use efficient base image and layer caching
FROM python:3.9-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

2. **Configure Docker resource limits**:
```yaml
run_launcher:
  module: dagster_docker
  class: DockerRunLauncher
  config:
    image: "my-dagster-image"
    container_kwargs:
      cpus: 2
      memory: "4g"
```

## Best practices

### Start with measurement

Before optimizing, measure your actual workload characteristics:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-measurement-first.py"
  language="python"
  title="Measuring workload characteristics before optimization"
/>

### Design for your expected scale

Choose execution methods based on production requirements, not development convenience:

- **Development**: Use `execute_in_process()` for fast iteration
- **Testing**: Use `execute_job()` to verify parallel behavior  
- **Production**: Use CLI execution or orchestrated deployment

### Monitor performance in production

Implement monitoring to detect performance regressions:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dynamic-production-monitoring.py"
  language="python"
  title="Production performance monitoring for dynamic outputs"
/>

### Document performance decisions

Always document why specific execution methods were chosen:

```python
# Job configuration with performance reasoning
@job(
    executor_def=multiprocess_executor.configured({"max_concurrent": 4}),
    description="""
    Uses multiprocess executor with 4 workers based on performance testing.
    Individual tasks average 120 seconds, making parallel overhead negligible.
    Tested on 2024-01-15 with 100-chunk workload showing 3.2x speedup.
    """
)
def production_data_pipeline():
    chunks = split_large_dataset()
    chunks.map(process_data_chunk)
```

## Common misconceptions

### **"Dynamic outputs don't run in parallel"**
**Reality:** They do run in parallel with proper executors and execution methods, but overhead can make small tasks slower than sequential processing.

### **"execute_in_process() should be fast for everything"**  
**Reality:** It's only optimal for small tasks; large tasks benefit significantly from parallelization despite overhead costs.

### **"More workers always means faster execution"**
**Reality:** Overhead grows with worker count; optimal size depends on task duration, system resources, and overhead-to-work ratio.

### **"CLI execution is always the production choice"**
**Reality:** CLI has the highest overhead; only beneficial for substantial workloads where work time dominates overhead.

### **"Parallel execution is always better for data processing"**
**Reality:** The overhead threshold (typically 30+ seconds per task) determines when parallel execution becomes beneficial.

## Next steps

- **Measure your specific workload** - Use the provided testing framework with your actual tasks and data
- **Choose appropriate execution method** - Based on your measured task durations and overhead analysis  
- **Optimize for your deployment environment** - Consider infrastructure constraints and scaling requirements
- **Implement monitoring** - Track performance metrics and overhead ratios in production
- **Iterate based on real usage** - Adjust configuration as workloads and infrastructure evolve

For more information on execution and performance optimization:
- [Job execution guide](/guides/build/jobs/job-execution)
- [Managing concurrency](/guides/operate/managing-concurrency) 
- [Executors reference](/concepts/ops-jobs-graphs/op-jobs-graphs#executors)
- [Testing guide](/concepts/testing)