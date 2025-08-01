# DagsterInstance Run Refactoring Plan

## Overview

This plan extracts run-related business logic from DagsterInstance into two simple files in a `runs` subfolder:

1. **`runs/run_implementation.py`** - Vanilla functions with moved business logic
2. **`runs/run_instance_ops.py`** - Simple wrapper class to provide clean interface

## Current State Analysis

### Run-Related Methods in DagsterInstance

Based on analysis of the current codebase, these methods need to be extracted:

**Public API Methods:**

- `create_run()` - Main run creation entry point
- `create_reexecuted_run()` - Creates reexecution runs
- `register_managed_run()` - Used by dagster-airflow

**Heavy Business Logic Methods:**

- `construct_run_with_snapshots()` - Complex run construction logic (~100+ lines)
- `_ensure_persisted_job_snapshot()` - Job snapshot persistence
- `_ensure_persisted_execution_plan_snapshot()` - Execution plan persistence
- `_get_keys_to_reexecute()` - Reexecution logic
- `_log_materialization_planned_event_for_asset()` - Asset event logging
- `log_asset_planned_events()` - Bulk asset event logging

### Private Dependencies

These methods access private DagsterInstance attributes/methods:

- `self._run_storage` - For run persistence
- `self._event_log_storage` - For event logging
- `self.report_engine_event()` - For engine events
- `self.report_dagster_event()` - For Dagster events
- `self.report_run_failed()` - For run failure reporting
- `self.get_run_by_id()` - For run retrieval
- `self.get_backfill()` - For backfill information
- `self.all_logs()` - For log retrieval
- `self` as DynamicPartitionsStore - For partition operations

## Implementation Plan

### Step 1: Create `runs/run_instance_ops.py`

Create a simple wrapper class that provides clean access to DagsterInstance capabilities:

```python
class RunInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for run operations."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    # Storage access
    @property
    def run_storage(self):
        return self._instance._run_storage  # noqa: SLF001

    @property
    def event_log_storage(self):
        return self._instance._event_log_storage  # noqa: SLF001

    # Event reporting
    def report_engine_event(self, message, dagster_run, event_data):
        return self._instance.report_engine_event(message, dagster_run, event_data)

    def report_dagster_event(self, event, run_id):
        return self._instance.report_dagster_event(event, run_id)

    def report_run_failed(self, dagster_run):
        return self._instance.report_run_failed(dagster_run)

    # Run operations
    def get_run_by_id(self, run_id):
        return self._instance.get_run_by_id(run_id)

    def get_backfill(self, backfill_id):
        return self._instance.get_backfill(backfill_id)

    def all_logs(self, run_id, of_type=None):
        return self._instance.all_logs(run_id, of_type)

    # DynamicPartitionsStore access
    def as_dynamic_partitions_store(self):
        return self._instance  # Instance implements DynamicPartitionsStore
```

**Key Points:**

- All `# noqa: SLF001` and `# type: ignore` annotations belong here
- No business logic - just trivial delegation
- Clean, simple interface for the business logic functions

### Step 2: Create `runs/run_implementation.py`

Move business logic to vanilla functions. Remove \_ prefixes so they can be invoked cross module.

```python
def create_run(
    ops: RunInstanceOps,
    *,
    job_name: str,
    run_id: Optional[str],
    # ... all the same parameters as current create_run
) -> DagsterRun:
    """Vanilla function with create_run business logic moved from DagsterInstance."""
    # Move all validation and business logic from DagsterInstance.create_run
    # Call construct_run_with_snapshots, handle asset events, etc.
    pass

def construct_run_with_snapshots(
    ops: RunInstanceOps,
    job_name: str,
    run_id: str,
    # ... all parameters
) -> DagsterRun:
    """Heavy run construction logic moved from DagsterInstance."""
    # Move the entire construct_run_with_snapshots method body
    # Use ops.run_storage, ops.event_log_storage etc. instead of self._*
    pass

def create_reexecuted_run(
    ops: RunInstanceOps,
    *,
    parent_run: DagsterRun,
    # ... all parameters
) -> DagsterRun:
    """Reexecution logic moved from DagsterInstance."""
    pass

def register_managed_run(
    ops: RunInstanceOps,
    job_name: str,
    # ... all parameters
) -> DagsterRun:
    """Managed run registration moved from DagsterInstance."""
    pass

# Helper functions (all the private methods)
def ensure_persisted_job_snapshot(ops: RunInstanceOps, job_snapshot, parent_job_snapshot):
    """Moved from DagsterInstance._ensure_persisted_job_snapshot"""
    pass

def ensure_persisted_execution_plan_snapshot(ops: RunInstanceOps, execution_plan_snapshot, job_snapshot_id, step_keys_to_execute):
    """Moved from DagsterInstance._ensure_persisted_execution_plan_snapshot"""
    pass

def get_keys_to_reexecute(ops: RunInstanceOps, run_id, execution_plan_snapshot):
    """Moved from DagsterInstance._get_keys_to_reexecute"""
    pass

def log_asset_planned_events(ops: RunInstanceOps, dagster_run, execution_plan_snapshot, asset_graph):
    """Moved from DagsterInstance.log_asset_planned_events"""
    pass

def log_materialization_planned_event_for_asset(ops: RunInstanceOps, dagster_run, asset_key, job_name, step, output, asset_graph):
    """Moved from DagsterInstance._log_materialization_planned_event_for_asset"""
    pass
```

**Key Points:**

- Functions take `RunInstanceOps` as first parameter instead of `self`
- Exact same business logic - just moved from methods to functions
- No naming changes, no logic changes
- Use `ops.run_storage` instead of `self._run_storage` etc.

### Step 3: Update DagsterInstance

Add simple delegation:

```python
from dagster._core.instance.runs import run_implementation

class DagsterInstance:
    # ... existing code ...

    @cached_property
    def _run_ops(self) -> RunInstanceOps:
        from dagster._core.instance.runs.run_instance_ops import RunInstanceOps
        return RunInstanceOps(self)

    def create_run(self, *, job_name, run_id, ...):
        """Delegate to run_implementation."""
        return run_implementation.create_run(
            self._run_ops,
            job_name=job_name,
            run_id=run_id,
            # ... pass all parameters
        )

    def create_reexecuted_run(self, *, parent_run, ...):
        """Delegate to run_implementation."""
        return run_implementation.create_reexecuted_run(
            self._run_ops,
            parent_run=parent_run,
            # ... pass all parameters
        )

    def register_managed_run(self, job_name, run_id, ...):
        """Delegate to run_implementation."""
        return run_implementation.register_managed_run(
            self._run_ops,
            job_name=job_name,
            run_id=run_id,
            # ... pass all parameters
        )
```

### Step 4: Clean Up

- Remove old business logic methods from DagsterInstance
- Remove any imports that are no longer needed
- Ensure the existing `run_operations.py` file still works (if it exists and is used elsewhere)

## Migration Benefits

1. **Encapsulation**: All private access is contained in `RunInstanceOps`
2. **Separation**: Business logic is cleanly separated from DagsterInstance
3. **Testability**: Functions can be unit tested with mock `RunInstanceOps`
4. **Maintainability**: Run logic is in focused files
5. **Backwards Compatibility**: All existing APIs work unchanged

## File Structure

```
python_modules/dagster/dagster/_core/instance/
├── instance.py                 # DagsterInstance with simple delegation
├── runs/
│   ├── __init__.py             # Empty init file
│   ├── run_instance_ops.py     # RunInstanceOps wrapper class
│   └── run_implementation.py   # Business logic functions
└── ...                         # Other existing files
```

## Implementation Steps

1. Create `runs/` subfolder with `__init__.py`
2. Create `runs/run_instance_ops.py` with wrapper class
3. Create `runs/run_implementation.py` with moved business logic
4. Update `DagsterInstance` to use `@cached_property` and delegate
5. Remove old business logic from `DagsterInstance`
6. Run `make ruff` and `make quick_pyright` to ensure clean code
7. Test that existing functionality works unchanged

## Key Design Principles

- **No business logic changes** - Just moving code around
- **All encapsulation violations contained** - In `RunInstanceOps` only
- **Simple delegation** - DagsterInstance becomes thin wrapper
- **Perfect backwards compatibility** - All existing APIs unchanged
- **Clean separation** - Business logic and instance concerns separated
