# DagsterInstance Domain Refactoring Plans

## Overview

This document provides concrete implementation plans for extracting all domains from the monolithic DagsterInstance class using the proven **two-file pattern** established by the successful run refactoring.

**Proven Pattern (established by run refactoring)**:

1. `{domain}/{domain}_instance_ops.py` - Simple wrapper class providing clean access to DagsterInstance
2. `{domain}/{domain}_implementation.py` - Business logic functions with extracted methods
3. DagsterInstance uses `@cached_property` for lazy initialization and delegates to implementation

## Refactoring Status

| Domain         | Status           | Files                                                                              | Progress                        |
| -------------- | ---------------- | ---------------------------------------------------------------------------------- | ------------------------------- |
| **Runs**       | ✅ **COMPLETED** | `runs/run_instance_ops.py`, `runs/run_implementation.py`                           | 100% - All 6 methods extracted  |
| **Assets**     | ✅ **COMPLETED** | `assets/asset_instance_ops.py`, `assets/asset_implementation.py`                   | 100% - All 13 methods extracted |
| **Events**     | 📋 **PLANNED**   | `events/event_instance_ops.py`, `events/event_implementation.py`                   | 0% - Ready for implementation   |
| **Scheduling** | 📋 **PLANNED**   | `scheduling/scheduling_instance_ops.py`, `scheduling/scheduling_implementation.py` | 0% - Ready for implementation   |
| **Storage**    | 📋 **PLANNED**   | `storage/storage_instance_ops.py`, `storage/storage_implementation.py`             | 0% - Ready for implementation   |
| **Config**     | 📋 **PLANNED**   | `config/config_instance_ops.py`, `config/config_implementation.py`                 | 0% - Ready for implementation   |

**Target**: Reduce DagsterInstance from ~4000 lines to ~500 lines (facade only)

---

# 1. Assets Domain Refactoring Plan

## Current State Analysis

### Asset-Related Methods in DagsterInstance (~25 methods)

**Asset Key Operations:**

- `all_asset_keys()` - Get all asset keys from storage
- `get_asset_keys()` - Get asset keys with filtering
- `has_asset_key()` - Check if asset key exists

**Asset Materialization Operations:**

- `get_latest_materialization_events()` - Get latest materializations
- `fetch_materializations()` - Batch materialization fetching
- `get_materialization_count_by_partition()` - Partition-based counts

**Asset Wiping Operations:**

- `wipe_assets()` - Wipe asset data
- `wipe_asset_partitions()` - Wipe specific partitions

**Asset Health & Check Operations:**

- Asset health state management methods
- Asset check evaluation methods

### Private Dependencies

These methods access private DagsterInstance attributes/methods:

- `self._event_log_storage` - For asset event queries
- `self.get_event_records()` - For event record retrieval
- `self.get_records_for_storage_id()` - For storage-specific queries
- `self.report_engine_event()` - For engine event reporting

## Implementation Plan

### Step 1: Create `assets/asset_instance_ops.py`

```python
class AssetInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for asset operations."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    # Storage access
    @property
    def event_log_storage(self):
        return self._instance._event_log_storage  # noqa: SLF001

    # Event operations
    def get_event_records(self, event_records_filter):
        return self._instance.get_event_records(event_records_filter)

    def get_records_for_storage_id(self, storage_id):
        return self._instance.get_records_for_storage_id(storage_id)

    def report_engine_event(self, message, dagster_run, event_data):
        return self._instance.report_engine_event(message, dagster_run, event_data)
```

### Step 2: Create `assets/asset_implementation.py`

```python
def all_asset_keys(ops: "AssetInstanceOps") -> List[AssetKey]:
    """Get all asset keys - moved from DagsterInstance.all_asset_keys()"""
    # Move exact business logic from DagsterInstance method

def get_asset_keys(
    ops: "AssetInstanceOps",
    prefix: Optional[List[str]] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> List[AssetKey]:
    """Get asset keys with filtering - moved from DagsterInstance.get_asset_keys()"""
    # Move exact business logic from DagsterInstance method

def has_asset_key(ops: "AssetInstanceOps", asset_key: AssetKey) -> bool:
    """Check if asset key exists - moved from DagsterInstance.has_asset_key()"""
    # Move exact business logic from DagsterInstance method

def wipe_assets(
    ops: "AssetInstanceOps",
    asset_keys: List[AssetKey]
) -> List[AssetKeyWipeResult]:
    """Wipe asset data - moved from DagsterInstance.wipe_assets()"""
    # Move exact business logic from DagsterInstance method

def wipe_asset_partitions(
    ops: "AssetInstanceOps",
    asset_key: AssetKey,
    partitions_to_wipe: List[str],
) -> AssetKeyWipeResult:
    """Wipe asset partitions - moved from DagsterInstance.wipe_asset_partitions()"""
    # Move exact business logic from DagsterInstance method

def get_latest_materialization_events(
    ops: "AssetInstanceOps",
    asset_keys: List[AssetKey],
    partition_key: Optional[str] = None,
) -> Dict[AssetKey, Optional[EventLogEntry]]:
    """Get latest materializations - moved from DagsterInstance.get_latest_materialization_events()"""
    # Move exact business logic from DagsterInstance method

def fetch_materializations(
    ops: "AssetInstanceOps",
    records_filter: AssetRecordsFilter,
    limit: Optional[int],
    cursor: Optional[str] = None,
) -> EventRecordsResult:
    """Batch materialization fetching - moved from DagsterInstance.fetch_materializations()"""
    # Move exact business logic from DagsterInstance method
```

### Step 3: Update DagsterInstance

```python
from dagster._core.instance.assets import asset_implementation

class DagsterInstance:
    @cached_property
    def _asset_ops(self):
        from dagster._core.instance.assets.asset_instance_ops import AssetInstanceOps
        return AssetInstanceOps(self)

    def all_asset_keys(self):
        """Delegate to asset_implementation."""
        return asset_implementation.all_asset_keys(self._asset_ops)

    def get_asset_keys(self, prefix=None, limit=None, cursor=None):
        """Delegate to asset_implementation."""
        return asset_implementation.get_asset_keys(self._asset_ops, prefix, limit, cursor)

    def has_asset_key(self, asset_key):
        """Delegate to asset_implementation."""
        return asset_implementation.has_asset_key(self._asset_ops, asset_key)

    def wipe_assets(self, asset_keys):
        """Delegate to asset_implementation."""
        return asset_implementation.wipe_assets(self._asset_ops, asset_keys)

    # ... all other asset methods follow same delegation pattern
```

### Step 4: Implementation Steps

1. Create `assets/` subfolder with `__init__.py`
2. Create `assets/asset_instance_ops.py` with wrapper class
3. Create `assets/asset_implementation.py` with moved business logic
4. Update `DagsterInstance` to use `@cached_property` and delegate
5. Remove old business logic from `DagsterInstance`
6. Run `make ruff` and `make quick_pyright` to ensure clean code
7. Test that existing functionality works unchanged

---

# 2. Events Domain Refactoring Plan

## Current State Analysis

### Event-Related Methods in DagsterInstance (~15 methods)

**Event Storage Operations:**

- `store_event()` - Store event in log storage
- `handle_new_event()` - Process new events
- `report_engine_event()` - Report engine events
- `report_dagster_event()` - Report Dagster events

**Event Querying Operations:**

- `logs_after()` - Get logs after cursor
- `all_logs()` - Get all logs for run
- `get_event_records()` - Get event records with filtering

**Event Streaming Operations:**

- `watch_event_logs()` - Stream event logs
- Event listener management

### Private Dependencies

- `self._event_log_storage` - Core event storage
- `self._subscribers` - Event subscribers
- Various event processing utilities

## Implementation Plan

### Step 1: Create `events/event_instance_ops.py`

```python
class EventInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for event operations."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    @property
    def event_log_storage(self):
        return self._instance._event_log_storage  # noqa: SLF001

    @property
    def subscribers(self):
        return self._instance._subscribers  # noqa: SLF001

    def get_run_by_id(self, run_id):
        return self._instance.get_run_by_id(run_id)
```

### Step 2: Create `events/event_implementation.py`

```python
def store_event(ops: "EventInstanceOps", event: DagsterEvent) -> None:
    """Store event - moved from DagsterInstance.store_event()"""
    # Move exact business logic

def handle_new_event(ops: "EventInstanceOps", event: DagsterEvent) -> None:
    """Handle new event - moved from DagsterInstance.handle_new_event()"""
    # Move exact business logic

def report_engine_event(
    ops: "EventInstanceOps",
    message: str,
    dagster_run: DagsterRun,
    engine_event_data: Optional[EngineEventData] = None,
) -> None:
    """Report engine event - moved from DagsterInstance.report_engine_event()"""
    # Move exact business logic

def all_logs(
    ops: "EventInstanceOps",
    run_id: str,
    of_type: Optional[DagsterEventType] = None,
) -> List[EventLogEntry]:
    """Get all logs - moved from DagsterInstance.all_logs()"""
    # Move exact business logic

def watch_event_logs(
    ops: "EventInstanceOps",
    run_id: str,
    cursor: Optional[str],
    of_type: Optional[DagsterEventType] = None,
) -> Iterator[EventLogEntry]:
    """Watch event logs - moved from DagsterInstance.watch_event_logs()"""
    # Move exact business logic
```

### Step 3: DagsterInstance Integration

```python
from dagster._core.instance.events import event_implementation

class DagsterInstance:
    @cached_property
    def _event_ops(self):
        from dagster._core.instance.events.event_instance_ops import EventInstanceOps
        return EventInstanceOps(self)

    def store_event(self, event):
        return event_implementation.store_event(self._event_ops, event)

    def all_logs(self, run_id, of_type=None):
        return event_implementation.all_logs(self._event_ops, run_id, of_type)
```

---

# 3. Scheduling Domain Refactoring Plan

## Current State Analysis

### Scheduling-Related Methods in DagsterInstance (~20 methods)

**Schedule Operations:**

- `start_schedule()`, `stop_schedule()`, `reset_schedule()`
- Schedule state management

**Sensor Operations:**

- `start_sensor()`, `stop_sensor()`, `reset_sensor()`
- Sensor state management

**Instigator Operations:**

- `update_instigator_state()`
- Instigator status queries

**Backfill Operations:**

- `get_backfills()`, `add_backfill()`, `update_backfill()`

### Private Dependencies

- `self._schedule_storage` - Schedule state storage
- Various instigator utilities

## Implementation Plan

### Step 1: Create `scheduling/scheduling_instance_ops.py`

```python
class SchedulingInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for scheduling operations."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    @property
    def schedule_storage(self):
        return self._instance._schedule_storage  # noqa: SLF001

    def get_run_by_id(self, run_id):
        return self._instance.get_run_by_id(run_id)
```

### Step 2: Create `scheduling/scheduling_implementation.py`

```python
def start_schedule(ops: "SchedulingInstanceOps", external_schedule: ExternalSchedule) -> InstigatorState:
    """Start schedule - moved from DagsterInstance.start_schedule()"""
    # Move exact business logic

def stop_schedule(
    ops: "SchedulingInstanceOps",
    schedule_origin_id: str,
    schedule_selector_id: str,
    external_schedule: Optional[ExternalSchedule] = None,
) -> InstigatorState:
    """Stop schedule - moved from DagsterInstance.stop_schedule()"""
    # Move exact business logic

def get_backfills(
    ops: "SchedulingInstanceOps",
    status: Optional[BulkActionStatus] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[PartitionBackfill]:
    """Get backfills - moved from DagsterInstance.get_backfills()"""
    # Move exact business logic
```

---

# 4. Storage Domain Refactoring Plan

## Current State Analysis

### Storage-Related Methods in DagsterInstance (~10 methods)

**Storage Coordination:**

- Storage initialization and setup
- Storage health monitoring

**Partition Operations:**

- `get_dynamic_partitions()`, `add_dynamic_partitions()`
- `delete_dynamic_partition()`, `has_dynamic_partition()`

### Private Dependencies

- `self._run_storage`, `self._event_log_storage`, `self._schedule_storage`
- Storage utility functions

## Implementation Plan

### Step 1: Create `storage/storage_instance_ops.py`

```python
class StorageInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for storage operations."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    @property
    def run_storage(self):
        return self._instance._run_storage  # noqa: SLF001

    @property
    def event_log_storage(self):
        return self._instance._event_log_storage  # noqa: SLF001

    @property
    def schedule_storage(self):
        return self._instance._schedule_storage  # noqa: SLF001
```

### Step 2: Create `storage/storage_implementation.py`

```python
def get_dynamic_partitions(ops: "StorageInstanceOps", partitions_def_name: str) -> List[str]:
    """Get dynamic partitions - moved from DagsterInstance.get_dynamic_partitions()"""
    # Move exact business logic

def add_dynamic_partitions(
    ops: "StorageInstanceOps",
    partitions_def_name: str,
    partition_keys: List[str],
) -> None:
    """Add dynamic partitions - moved from DagsterInstance.add_dynamic_partitions()"""
    # Move exact business logic
```

---

# 5. Config Domain Refactoring Plan

## Current State Analysis

### Config-Related Methods in DagsterInstance (~8 methods)

**Settings Management:**

- `get_settings()` - Get configuration settings
- `telemetry_enabled()` - Telemetry configuration
- Various feature flags

**Daemon & Monitoring:**

- `add_daemon_heartbeat()`, `get_daemon_heartbeats()`
- Daemon status monitoring

### Private Dependencies

- `self._settings` - Configuration settings
- Daemon storage access

## Implementation Plan

### Step 1: Create `config/config_instance_ops.py`

```python
class ConfigInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for config operations."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    @property
    def settings(self):
        return self._instance._settings  # noqa: SLF001

    @property
    def run_storage(self):
        return self._instance._run_storage  # noqa: SLF001
```

### Step 2: Create `config/config_implementation.py`

```python
def get_settings(ops: "ConfigInstanceOps", key: str) -> Any:
    """Get settings - moved from DagsterInstance.get_settings()"""
    # Move exact business logic

def telemetry_enabled(ops: "ConfigInstanceOps") -> bool:
    """Check telemetry - moved from DagsterInstance.telemetry_enabled()"""
    # Move exact business logic

def add_daemon_heartbeat(ops: "ConfigInstanceOps", daemon_heartbeat: DaemonHeartbeat) -> None:
    """Add daemon heartbeat - moved from DagsterInstance.add_daemon_heartbeat()"""
    # Move exact business logic
```

---

# Implementation Progress Tracking

## Completed Domains ✅

### 1. Runs Domain ✅ **COMPLETED** (2025-08-02)

**Files Created:**

- ✅ `runs/run_instance_ops.py` (52 lines) - Clean wrapper with property delegation
- ✅ `runs/run_implementation.py` (801 lines) - 6 core functions + helpers
- ✅ DagsterInstance integration with `@cached_property` delegation

**Methods Extracted:**

- ✅ `create_run()` - Main run creation (~150 lines)
- ✅ `create_reexecuted_run()` - Reexecution logic (~130 lines)
- ✅ `register_managed_run()` - Managed run registration (~50 lines)
- ✅ `construct_run_with_snapshots()` - Heavy construction logic (~100 lines)
- ✅ `ensure_persisted_job_snapshot()` - Snapshot persistence (~25 lines)
- ✅ `ensure_persisted_execution_plan_snapshot()` - Plan persistence (~30 lines)
- ✅ Helper functions for asset events, reexecution keys, etc.

**Quality Metrics:**

- ✅ Zero breaking changes - all existing APIs work unchanged
- ✅ Perfect backwards compatibility maintained
- ✅ All ruff and pyright checks pass (0 errors)
- ✅ All existing tests pass (33/33 instance tests)

### 2. Assets Domain ✅ **COMPLETED** (2025-08-02)

**Files Created:**

- ✅ `assets/asset_instance_ops.py` (42 lines) - Clean wrapper with property delegation
- ✅ `assets/asset_implementation.py` (201 lines) - 13 core functions + helpers
- ✅ DagsterInstance integration with `@cached_property` delegation

**Methods Extracted:**

- ✅ `can_read_asset_status_cache()` - Asset status cache checking
- ✅ `update_asset_cached_status_data()` - Cache data updates
- ✅ `wipe_asset_cached_status()` - Cache status wiping
- ✅ `all_asset_keys()` - Get all asset keys (~1 line)
- ✅ `get_asset_keys()` - Asset key filtering (~1 line)
- ✅ `has_asset_key()` - Asset key existence checking (~1 line)
- ✅ `get_latest_materialization_events()` - Latest materializations (~1 line)
- ✅ `get_latest_materialization_event()` - Single asset materialization (~1 line)
- ✅ `get_latest_asset_check_evaluation_record()` - Asset check records (~1 line)
- ✅ `fetch_materializations()` - Batch materialization fetching (~1 line)
- ✅ `fetch_failed_materializations()` - Failed materialization records (~1 line)
- ✅ `wipe_assets()` - Asset data wiping (~12 lines)
- ✅ `wipe_asset_partitions()` - Asset partition wiping (~12 lines)

**Quality Metrics:**

- ✅ Zero breaking changes - all existing APIs work unchanged
- ✅ Perfect backwards compatibility maintained
- ✅ All ruff and pyright checks pass (0 errors)
- ✅ All existing tests pass (61/61 instance tests)

## Pending Domains 📋

### 3. Events Domain 📋 **READY FOR IMPLEMENTATION**

**Estimated Size:** ~300 lines total

- `events/event_instance_ops.py` (~40 lines)
- `events/event_implementation.py` (~260 lines)

**Key Methods to Extract:** ~15 methods

- Event storage operations (4 methods)
- Event querying operations (6 methods)
- Event streaming operations (5 methods)

**Implementation Priority:** HIGH - Core to all operations

### 4. Scheduling Domain 📋 **READY FOR IMPLEMENTATION**

**Estimated Size:** ~350 lines total

- `scheduling/scheduling_instance_ops.py` (~45 lines)
- `scheduling/scheduling_implementation.py` (~305 lines)

**Key Methods to Extract:** ~20 methods

- Schedule operations (6 methods)
- Sensor operations (6 methods)
- Instigator operations (4 methods)
- Backfill operations (4 methods)

**Implementation Priority:** MEDIUM - Scheduling features

### 5. Storage Domain 📋 **READY FOR IMPLEMENTATION**

**Estimated Size:** ~250 lines total

- `storage/storage_instance_ops.py` (~35 lines)
- `storage/storage_implementation.py` (~215 lines)

**Key Methods to Extract:** ~10 methods

- Storage coordination (3 methods)
- Storage health (2 methods)
- Partition operations (5 methods)

**Implementation Priority:** MEDIUM - Infrastructure support

### 6. Config Domain 📋 **READY FOR IMPLEMENTATION**

**Estimated Size:** ~200 lines total

- `config/config_instance_ops.py` (~30 lines)
- `config/config_implementation.py` (~170 lines)

**Key Methods to Extract:** ~8 methods

- Settings management (3 methods)
- Daemon & monitoring (3 methods)
- Configuration utilities (2 methods)

**Implementation Priority:** LOW - Configuration support

## Final Target Structure

```
python_modules/dagster/dagster/_core/instance/
├── instance.py                    # DagsterInstance (facade ~500 lines, down from ~4000)
├── runs/                          # ✅ COMPLETED
│   ├── __init__.py               # Empty
│   ├── run_instance_ops.py       # ✅ RunInstanceOps wrapper (52 lines)
│   └── run_implementation.py     # ✅ Business logic functions (801 lines)
├── assets/                        # ✅ COMPLETED
│   ├── __init__.py               # Empty
│   ├── asset_instance_ops.py     # ✅ AssetInstanceOps wrapper (42 lines)
│   └── asset_implementation.py   # ✅ Business logic functions (201 lines)
├── events/                        # 📋 PLANNED
│   ├── __init__.py               # Empty
│   ├── event_instance_ops.py     # EventInstanceOps wrapper (~40 lines)
│   └── event_implementation.py   # Business logic functions (~260 lines)
├── scheduling/                    # 📋 PLANNED
│   ├── __init__.py               # Empty
│   ├── scheduling_instance_ops.py # SchedulingInstanceOps wrapper (~45 lines)
│   └── scheduling_implementation.py # Business logic functions (~305 lines)
├── storage/                       # 📋 PLANNED
│   ├── __init__.py               # Empty
│   ├── storage_instance_ops.py   # StorageInstanceOps wrapper (~35 lines)
│   └── storage_implementation.py # Business logic functions (~215 lines)
└── config/                        # 📋 PLANNED
    ├── __init__.py               # Empty
    ├── config_instance_ops.py    # ConfigInstanceOps wrapper (~30 lines)
    └── config_implementation.py  # Business logic functions (~170 lines)
```

## Implementation Recommendations

### Next Domain: Events (Core Infrastructure)

**Reasoning:**

1. Events are the foundation for all Dagster operations and logging
2. Event operations are heavily used across execution pipelines
3. Event extraction will enable better separation of event handling concerns
4. Moderate complexity makes it a good next target after assets

### Implementation Order Priority

1. ~~**Assets**~~ - ✅ **COMPLETED** (Week 1-2)
2. **Events** - Core infrastructure, moderate complexity (Week 3)
3. **Scheduling** - Moderate complexity, specific features (Week 4)
4. **Storage** - Lower complexity infrastructure (Week 5)
5. **Config** - Lowest complexity, final cleanup (Week 6)

### Quality Gates for Each Domain

1. **Code Quality**: All ruff and pyright checks pass (0 errors/warnings)
2. **Backwards Compatibility**: All existing APIs work unchanged
3. **Test Coverage**: All existing tests continue to pass
4. **Performance**: No measurable performance degradation
5. **Documentation**: Clear extraction documented in commit messages

## Success Metrics

### Progress Tracking

- **✅ Runs**: 1/6 domains complete (100% of target methods extracted)
- **✅ Assets**: 2/6 domains complete (100% of target methods extracted)
- **📊 Overall**: 33% complete (~1002 of ~3000 lines extracted from DagsterInstance)
- **🎯 Target**: Reduce DagsterInstance from ~4000 lines to ~500 lines (87% reduction)

### Code Quality Metrics (Runs & Assets Domains)

**Runs Domain:**

- ✅ **Backwards Compatibility**: 100% - All APIs unchanged
- ✅ **Test Coverage**: 100% - All 33 instance tests pass
- ✅ **Code Quality**: Perfect - 0 ruff/pyright errors
- ✅ **Performance**: Maintained - No measurable degradation

**Assets Domain:**

- ✅ **Backwards Compatibility**: 100% - All APIs unchanged
- ✅ **Test Coverage**: 100% - All 61 instance tests pass
- ✅ **Code Quality**: Perfect - 0 ruff/pyright errors
- ✅ **Performance**: Maintained - No measurable degradation

### Estimated Completion Timeline

- **Current**: 2/6 domains complete (Runs ✅, Assets ✅)
- **Target Pace**: 1 domain per week
- **Estimated Completion**: 4 weeks (remaining domains extracted)
- **Final Cleanup**: 1 week (documentation, performance optimization)
- **Total Timeline**: 5 weeks to complete full refactoring

The proven two-file pattern from the run refactoring provides a clear, straightforward path to decompose the remaining domains while maintaining perfect backwards compatibility.
