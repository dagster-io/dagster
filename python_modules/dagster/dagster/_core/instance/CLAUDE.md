# DagsterInstance Architecture: Domains vs Mixins

This document explains the architectural patterns used to organize the `DagsterInstance` class.

## Mixins

**Purpose**: Organize DagsterInstance surface area and API methods.

**Implementation**: Mixins should contain trivial implementations - primarily property accessors, setting getters, and simple method delegations. They exist to keep the main `DagsterInstance` class manageable by grouping related surface area.

**Examples**:

- `SettingsMixin` - Contains properties and getters for various instance settings
- Future mixins might organize other surface area like telemetry methods, debugging utilities, etc.

**Key Principle**: Mixins should NOT contain complex business logic. They are organizational tools for the public API.

## Domains

**Purpose**: Organize the business logic of DagsterInstance into focused, cohesive modules.

**Implementation**: Domains contain the meaningful business logic and complex operations. Each domain is a separate class that encapsulates a specific area of functionality.

**Examples**:

- `RunDomain` - Business logic for run creation, management, and lifecycle
- `AssetDomain` - Business logic for asset operations and queries
- `EventDomain` - Business logic for event handling and storage
- `StorageDomain` - Business logic for storage operations
- `SchedulingDomain` - Business logic for schedules and sensors
- `DaemonDomain` - Business logic for daemon operations

**Key Principle**: This is where complex algorithms, validation, coordination between storage systems, and other meaningful business logic should be implemented.

## Usage Pattern

1. **DagsterInstance** inherits from mixins to expose organized surface area
2. **DagsterInstance** creates domain instances as cached properties (e.g., `_run_domain`, `_asset_domain`)
3. **Mixin methods** delegate to appropriate domain methods when business logic is needed
4. **Domain methods** contain the actual implementation logic

This separation keeps the codebase organized, testable, and maintainable while preserving a clean public API on `DagsterInstance`.
