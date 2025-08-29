---
created: 2025-08-29
title: "Internal Dagster Cloud GraphQL Usage Patterns"
description: "Comprehensive documentation of asset health and stateful GraphQL queries used in internal Dagster Cloud frontend"
---

# Internal GraphQL Usage Documentation

## Maintenance Strategy

**To update or recreate this document:**

1. **Analysis Prompt:** "Analyze `internal/dagster-cloud/js_modules/app-cloud/src/` for GraphQL usage patterns across the entire Dagster Plus ontology including assets, runs, jobs, schedules, sensors, deployments, teams, users, alerts, insights, and all other entities"

2. **Search Commands:**

   ```bash
   # Find all GraphQL fragments and queries
   grep -r "fragment.*\|query.*\|mutation.*\|subscription.*" internal/dagster-cloud/js_modules/app-cloud/src/

   # Find entity-specific usage patterns
   grep -r "AssetHealth\|RunStatus\|JobStatus\|ScheduleStatus\|SensorStatus" internal/dagster-cloud/js_modules/app-cloud/src/
   grep -r "DeploymentStatus\|AgentStatus\|CodeLocationStatus" internal/dagster-cloud/js_modules/app-cloud/src/
   grep -r "AlertPolicy\|TeamPermissions\|UserRole" internal/dagster-cloud/js_modules/app-cloud/src/

   # Find data providers and fragments
   grep -r "DataProvider\|Fragment" internal/dagster-cloud/js_modules/app-cloud/src/
   ```

3. **Focus Areas:**
   - `src/assets/` + `src/asset-health/` - Asset catalog, health, and materialization patterns
   - `src/runs/` - Run execution, status, and metrics
   - `src/jobs/` + `src/pipelines/` - Job/pipeline definition and execution patterns
   - `src/schedules/` + `src/sensors/` - Automation and triggering patterns
   - `src/code-location/` - Code location management and server metrics
   - `src/deployment/` + `src/deployment-switcher/` - Deployment management and environment variables
   - `src/health/` - Agent and daemon health monitoring
   - `src/insights/` - Metrics, cost tracking, and performance analytics
   - `src/home/` - Dashboard aggregations and summary views
   - `src/settings/` - Organization settings, tokens, and configuration
   - `src/teams/` + `src/users/` + `src/roles/` + `src/permissions/` - RBAC and user management
   - `src/catalog-view/` - Asset catalog views and favorites
   - `src/onboarding-checklist/` - Setup and configuration workflows
   - `src/serverless/` - Serverless deployment patterns
   - `src/graphql/schema.graphql` - Complete GraphQL schema reference

4. **Update Process:** Re-run analysis whenever internal app introduces new GraphQL usage patterns for any entity or when planning new API endpoints. Focus on production usage patterns to ensure API consistency across the entire Dagster Plus ontology.

## **IMPORTANT: Deprecated "Pipeline" Terminology**

**⚠️ Avoid Pipeline Language in dg API Implementation**

The GraphQL schema and internal frontend still contain legacy "pipeline" terminology that should **NOT** be exposed in new `dg api` commands. When implementing APIs:

- **Use "Job" terminology** exclusively in user-facing APIs, even when underlying GraphQL uses `pipelineName`
- **Filter/translate** any pipeline references to job terminology in outputs
- **Only use pipeline GraphQL fields** when they are the sole source of required information
- **Hide pipeline terminology** from users through API abstraction layers

This ensures `dg api` uses current Dagster language conventions while maintaining compatibility with existing GraphQL schemas.

---

## Standard Practice Documentation

**Source of Truth:** The `internal/` directory contains the production Dagster Cloud frontend which serves as the authoritative reference for GraphQL usage patterns in Dagster Plus. When implementing new API endpoints in `dagster-dg-cli`, always check internal usage first to ensure consistency with production patterns.

---

## Table of Contents by Ontology Group

| Entity Group                          | OSS | Plus | Status      | Location in Doc                                                                                          | Key Types                                                                  |
| ------------------------------------- | --- | ---- | ----------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **Assets & Asset Health**             | ✅  | ✅   | ✅ Complete | [Asset Health GraphQL Schema Overview](#asset-health-graphql-schema-overview)                            | `AssetNode`, `AssetHealth`, `AssetFreshnessInfo`                           |
| **Runs & Execution**                  | ✅  | ✅   | ✅ Complete | [Runs and Execution GraphQL Patterns](#runs-and-execution-graphql-patterns)                              | `Run`, `RunStatus`, `RunStatsSnapshot`                                     |
| **Jobs & Pipelines**                  | ✅  | ✅   | ✅ Complete | [Jobs and Pipelines GraphQL Patterns](#jobs-and-pipelines-graphql-patterns)                              | `Job`, `JobReportingMetrics`, `QualifiedJob`                               |
| **Schedules & Sensors**               | ✅  | ✅   | ✅ Complete | [Schedules and Sensors (Automation)](#schedules-and-sensors-automation)                                  | `Schedule`, `Sensor`, `InstigationStatus`                                  |
| **Backfills & Partitions**            | ✅  | ✅   | ✅ Complete | [Backfills and Partitions GraphQL Patterns](#backfills-and-partitions-graphql-patterns)                  | `PartitionBackfill`, `BackfillPolicy`, `AssetPartitions`                   |
| **Instance & Daemon Health**          | ✅  | ✅   | ✅ Complete | [Instance and Daemon Health GraphQL Patterns](#instance-and-daemon-health-graphql-patterns)              | `Instance`, `DaemonHealth`, `RunLauncher`                                  |
| **Asset Checks & Evaluations**        | ✅  | ✅   | ✅ Complete | [Asset Checks and Evaluations GraphQL Patterns](#asset-checks-and-evaluations-graphql-patterns)          | `AssetCheck`, `AssetConditionEvaluation`, `AutoMaterializeAssetEvaluation` |
| **Resources & Configuration**         | ✅  | ✅   | ✅ Complete | [Resources and Configuration GraphQL Patterns](#resources-and-configuration-graphql-patterns)            | `Resource`, `RunConfigSchema`, `EnvVarsOrError`                            |
| **Deployments & Environments**        | ❌  | ✅   | ✅ Complete | [Deployments and Environment Management](#deployments-and-environment-management)                        | `DagsterCloudDeployment`, `WorkspaceEntry`                                 |
| **Agents & Code Locations**           | ❌  | ✅   | ✅ Complete | [Agent and Code Location Health](#agent-and-code-location-health)                                        | `Agent`, `CodeServerState`                                                 |
| **Insights & Metrics**                | ❌  | ✅   | ✅ Complete | [Insights and Metrics GraphQL Patterns](#insights-and-metrics-graphql-patterns)                          | `ReportingEntry`, `MetricType`, `ReportingMetrics`                         |
| **Alerts & Notifications**            | ❌  | ✅   | ✅ Complete | [Alerts & Notifications GraphQL Patterns](#alerts--notifications-graphql-patterns)                       | `AlertPolicy`, `AlertNotification`                                         |
| **Teams & Users & RBAC**              | ❌  | ✅   | ✅ Complete | [Teams & Users & RBAC GraphQL Patterns](#teams--users--rbac-graphql-patterns)                            | `Team`, `User`, `Role`, `Permission`                                       |
| **Tokens & Authentication**           | ❌  | ✅   | ✅ Complete | [Tokens & Authentication GraphQL Patterns](#tokens--authentication-graphql-patterns)                     | `APIToken`, `AgentToken`, `UserToken`                                      |
| **Settings & Configuration**          | ❌  | ✅   | ✅ Complete | [Settings & Configuration GraphQL Patterns](#settings--configuration-graphql-patterns)                   | `OrganizationSettings`, `FeatureFlags`                                     |
| **Catalog Views & Favorites**         | ❌  | ✅   | ✅ Complete | [Catalog Views & Favorites GraphQL Patterns](#catalog-views--favorites-graphql-patterns)                 | `CatalogView`, `FavoriteAssets`                                            |
| **Onboarding & Setup**                | ❌  | ✅   | ✅ Complete | [Onboarding & Setup GraphQL Patterns](#onboarding--setup-graphql-patterns)                               | `OnboardingChecklist`, `SetupWorkflow`                                     |
| **Serverless & Cloud Infrastructure** | ❌  | ✅   | ✅ Complete | [Serverless & Cloud Infrastructure GraphQL Patterns](#serverless--cloud-infrastructure-graphql-patterns) | `ServerlessInfo`, `ContainerMetrics`                                       |

**Legend:**

- **OSS**: ✅ Available in Dagster Open Source, ❌ Plus/Cloud only
- **Plus**: ✅ Available in Dagster Plus/Cloud
- **Status**: ✅ Complete - Full schema types, fragments, and production usage patterns documented, 🟡 Partial - Basic types documented, needs more usage patterns and fragments, ❌ Not Started - Needs full analysis and documentation

---

## OSS vs Plus GraphQL API Comparison

### Core Capabilities Available in Both OSS and Plus

The following entity groups provide robust GraphQL APIs in both OSS and Plus deployments:

**Operational APIs (High dg CLI API Priority)**:

- **Assets & Asset Health**: Complete asset lifecycle management, health monitoring, freshness tracking
- **Runs & Execution**: Run launching, monitoring, termination, execution plans
- **Jobs & Pipelines**: Job management, execution history, configuration
- **Schedules & Sensors**: Automation control, state management, tick monitoring
- **Backfills & Partitions**: Bulk operations, partition targeting, status tracking
- **Instance & Daemon Health**: System monitoring, configuration, concurrency management

**Advanced Features (Medium dg CLI API Priority)**:

- **Asset Checks & Evaluations**: Data quality validation, auto-materialization policies
- **Resources & Configuration**: Resource management, environment variables, run configuration

### Plus-Only Extensions

**Cloud-Specific APIs (Plus dg CLI API Priority)**:

- **Deployments & Environments**: Multi-tenant deployment management
- **Agents & Code Locations**: Cloud infrastructure monitoring
- **Insights & Metrics**: Usage analytics, cost tracking, performance monitoring
- **Alerts & Notifications**: Policy-based alerting, multi-channel notifications
- **Teams & Users & RBAC**: User management, permission systems, audit trails
- **Tokens & Authentication**: API token management, scoped permissions
- **Settings & Configuration**: Organization settings, feature flags
- **Catalog Views & Favorites**: Personal asset management, custom views
- **Onboarding & Setup**: Guided setup workflows, integration tracking
- **Serverless & Cloud Infrastructure**: Auto-scaling, cloud provider integration

---

## OSS GraphQL Schema Analysis

### Comprehensive Schema Coverage Analysis

Through systematic analysis of the Dagster OSS GraphQL schema in `python_modules/dagster-graphql/dagster_graphql/schema/`, we've identified extensive API surface area suitable for dg CLI integration. The OSS schema provides production-ready GraphQL types across all major Dagster operational domains.

### Key OSS Schema Files Analyzed

| Schema File              | Key Types                                                    | API Coverage                                 | dg CLI Priority |
| ------------------------ | ------------------------------------------------------------ | -------------------------------------------- | --------------- |
| `runs.py`                | `Run`, `RunStatus`, `RunStats`, `RunStepStats`               | Complete run lifecycle management            | **High**        |
| `schedules/schedules.py` | `Schedule`, `ScheduleState`, `ScheduleTick`                  | Schedule automation and monitoring           | **High**        |
| `sensors.py`             | `Sensor`, `SensorState`, `SensorResult`                      | Sensor-based automation control              | **High**        |
| `backfill.py`            | `PartitionBackfill`, `BulkActionStatus`, `AssetBackfillData` | Backfill operations and partition management | **High**        |
| `asset_health.py`        | `AssetHealth`, `AssetHealthStatus`, async resolvers          | Asset monitoring and health tracking         | **High**        |
| `instance.py`            | `Instance`, `DaemonHealth`, `ConcurrencyKeyInfo`             | System health and configuration              | **High**        |
| `resources.py`           | `ResourceDetails`, `ConfiguredValue`, nested dependencies    | Resource management and configuration        | **Medium-High** |
| `config_types.py`        | `ConfigType`, `CompositeConfigType`, type introspection      | Configuration schema analysis                | **Medium**      |

### OSS GraphQL Type Coverage Summary

**Production-Ready OSS Types (347+ types analyzed)**:

1. **Core Execution Types** (87 types):
   - Run management: `Run`, `RunConnection`, `RunStatus`, `RunStatsSnapshot`
   - Step execution: `ExecutionStep`, `StepEvent`, `StepMaterialization`
   - Plan execution: `ExecutionPlan`, `ExecutionStepInput`, `ExecutionStepOutput`

2. **Asset Management Types** (64 types):
   - Asset nodes: `AssetNode`, `AssetConnection`, `AssetMaterialization`
   - Asset health: `AssetHealth`, `AssetHealthStatus`, health metadata unions
   - Asset keys: `AssetKey`, `AssetSelection`, `AssetGroup`

3. **Automation Types** (43 types):
   - Schedules: `Schedule`, `ScheduleState`, `ScheduleTick`, `ScheduleConnection`
   - Sensors: `Sensor`, `SensorState`, `SensorResult`, `SensorConnection`
   - Auto-materialize: `AutoMaterializePolicy`, `AutoMaterializeRule`, evaluation records

4. **Backfill and Partition Types** (38 types):
   - Backfills: `PartitionBackfill`, `PartitionBackfillPolicy`, status tracking
   - Partitions: `Partition`, `PartitionSet`, `PartitionStatus`, `PartitionRun`
   - Bulk operations: `BulkActionStatus`, `LaunchBackfillSuccess`, bulk mutations

5. **System Health Types** (29 types):
   - Instance: `Instance`, `InstanceInfo`, configuration management
   - Daemons: `DaemonHealth`, `DaemonStatus`, heartbeat monitoring
   - Concurrency: `ConcurrencyKeyInfo`, `ClaimedConcurrencySlot`, queue management

6. **Resource and Configuration Types** (34 types):
   - Resources: `ResourceDetails`, `NestedResourceEntry`, usage tracking
   - Config: `ConfigType`, `ConfigTypeField`, `CompositeConfigType`, validation
   - Environment: `ConfiguredValue`, `ConfiguredValueType`, env var management

7. **Asset Check Types** (23 types):
   - Checks: `AssetCheck`, `AssetCheckExecution`, `AssetCheckEvaluation`
   - Results: `AssetCheckResult`, `AssetCheckSeverity`, metadata integration
   - Conditions: `AssetConditionEvaluation`, condition nodes, subset operations

8. **Job and Pipeline Types** (29 types):
   - Jobs: `Job`, `JobState`, `JobConnection`, execution management
   - Pipelines: `Pipeline`, `PipelineRun`, mode configuration
   - Operations: `SolidDefinition`, `CompositeSolidDefinition`, op metadata

### OSS API Completeness Assessment

**Fully Complete Categories** (Ready for dg CLI APIs):

✅ **Run Management**: Complete CRUD operations, status tracking, termination, execution plans  
✅ **Asset Operations**: Full lifecycle management, health monitoring, materialization tracking  
✅ **Schedule Control**: Start/stop operations, tick monitoring, state management  
✅ **Sensor Management**: Activation control, result processing, cursor management  
✅ **Backfill Operations**: Launch/cancel/resume, partition targeting, status monitoring  
✅ **Instance Health**: Daemon monitoring, configuration introspection, concurrency management  
✅ **Resource Discovery**: Configuration analysis, dependency tracking, usage mapping

**Partially Complete Categories** (Suitable for focused dg CLI APIs):

🟡 **Asset Health**: Health status available, but some metadata resolution requires async processing  
🟡 **Configuration Management**: Schema introspection complete, validation workflows need development  
🟡 **Auto-Materialization**: Policy evaluation available, but debugging tools could be enhanced

**Key OSS Schema Strengths**:

1. **Comprehensive Mutation Support**: All major operations (launch, terminate, cancel) have corresponding mutations
2. **Rich Metadata Integration**: Events, logs, and metadata are deeply integrated across all types
3. **Connection-Based Pagination**: Proper cursor-based pagination for all list operations
4. **Type Safety**: Strong typing with unions and interfaces for error handling
5. **Async Support**: Asset health and condition evaluations use proper async resolvers

**Unique OSS Capabilities Not Available in Plus APIs**:

- **Deep Configuration Introspection**: Complete config type system with recursive analysis
- **Resource Dependency Mapping**: Full nested resource relationship traversal
- **Daemon Health Details**: Individual daemon status and heartbeat monitoring
- **Asset Condition Debugging**: Detailed condition evaluation trees with subset analysis
- **Local Instance Management**: Direct instance configuration and control

### dg CLI API Development Strategy Based on OSS Analysis

**Immediate High-Value Opportunities**:

1. **Core Operations APIs** - Leverage complete OSS run, asset, and automation management
2. **System Monitoring APIs** - Utilize comprehensive health and daemon status information
3. **Bulk Operations APIs** - Take advantage of sophisticated backfill and partition management
4. **Configuration APIs** - Exploit rich resource and config introspection capabilities

**Implementation Advantages**:

- **No Cloud Dependencies**: All analyzed types work in pure OSS environments
- **Production-Proven**: Types are actively used in production Dagster OSS deployments
- **Complete Documentation**: Schema types include comprehensive descriptions and examples
- **Error Handling**: Proper union types for error scenarios across all operations

This analysis confirms that Dagster OSS provides a remarkably complete GraphQL API surface suitable for comprehensive dg CLI implementation across all major operational domains.

---

## Asset Health GraphQL Schema Overview

### Core Asset Health Type

```graphql
type AssetHealth {
  assetHealth: AssetHealthStatus! # Overall health status
  materializationStatus: AssetHealthStatus! # Materialization execution status
  materializationStatusMetadata: AssetHealthMaterializationMeta
  assetChecksStatus: AssetHealthStatus! # Asset checks status
  assetChecksStatusMetadata: AssetHealthCheckMeta
  freshnessStatus: AssetHealthStatus! # Data freshness status
  freshnessStatusMetadata: AssetHealthFreshnessMeta
}

enum AssetHealthStatus {
  HEALTHY
  WARNING
  DEGRADED
  UNKNOWN
  NOT_APPLICABLE
}
```

### Stateful Asset Information Available

```graphql
type AssetNode {
  # Materialization History
  latestMaterializationByPartition(
    partitions: [String!]
  ): [MaterializationEvent]!
  assetMaterializations(
    partitions: [String!]
    beforeTimestampMillis: String
    limit: Int
  ): [MaterializationEvent!]!

  # Freshness Information
  freshnessInfo: AssetFreshnessInfo
  freshnessPolicy: FreshnessPolicy
  freshnessStatusInfo: FreshnessStatusInfo

  # Partition Status
  assetPartitionStatuses: AssetPartitionStatuses!
  partitionStats: PartitionStats

  # Health Integration
  assetHealth: AssetHealth # Available on Asset type, not AssetNode
}

type AssetFreshnessInfo {
  currentLagMinutes: Float
  currentMinutesLate: Float
  latestMaterializationMinutesLate: Float
}

type FreshnessPolicy {
  maximumLagMinutes: Float!
  cronSchedule: String
  cronScheduleTimezone: String
  lastEvaluationTimestamp: String
}
```

## Production Usage Patterns

### 1. Home Dashboard - Degraded Assets Classification

**Location:** `src/home/DegradedAssetsList.tsx`

**Pattern:** Categorizes assets by health status type

```typescript
// Asset health status checking
if (node.assetHealth?.materializationStatus === AssetHealthStatus.DEGRADED) {
  byType[DegradedType.MATERIALIZATION_FAILURES].push(node);
}
if (node.assetHealth?.freshnessStatus === AssetHealthStatus.DEGRADED) {
  byType[DegradedType.FRESHNESS_FAILURES].push(node);
}
if (node.assetHealth?.assetChecksStatus === AssetHealthStatus.DEGRADED) {
  byType[DegradedType.CHECK_FAILURES].push(node);
}
if (node.assetHealth?.freshnessStatus === AssetHealthStatus.WARNING) {
  byType[DegradedType.FRESHNESS_WARNINGS].push(node);
}
if (node.assetHealth?.assetChecksStatus === AssetHealthStatus.WARNING) {
  byType[DegradedType.CHECK_WARNINGS].push(node);
}
```

**GraphQL Fragment Used:**

```typescript
// From AssetHealthDataProvider - gets comprehensive health data
const AssetHealthFragment = gql`
  fragment AssetHealth on Asset {
    id
    key {
      path
    }
    assetHealth {
      assetHealth
      materializationStatus
      materializationStatusMetadata {
        __typename
        ... on AssetHealthMaterializationDegradedPartitionedMeta {
          numFailedPartitions
          numMissingPartitions
          totalNumPartitions
        }
        ... on AssetHealthMaterializationDegradedNotPartitionedMeta {
          failedRunId
        }
      }
      freshnessStatus
      freshnessStatusMetadata {
        lastMaterializedTimestamp
      }
      assetChecksStatus
      assetChecksStatusMetadata {
        __typename
        ... on AssetHealthCheckDegradedMeta {
          numFailedChecks
          numWarningChecks
          totalNumChecks
        }
      }
    }
  }
`;
```

### 2. Asset Health Overview - Detailed Status Categorization

**Location:** `src/asset-health/buildAssetHealthSections.tsx`

**Pattern:** Provides detailed reasoning for asset health status with interactive elements

```typescript
// Materialization failure reasoning with partition details
if (numFailed > 0) {
  return (
    <Tag>
      <Box flex={{gap: 4}}>
        <Icon name="error_outline" color={Colors.accentRed()} />
        <Link to={assetDetailsPathForKey(asset.key, {
          status: AssetPartitionStatus.FAILED,
          view: 'partitions',
        })}>
          {numFailed === 1 ? `1 partition` : `${numFailed} partitions`}
        </Link>
      </Box>
    </Tag>
  );
}

// Run failure with timestamp
if (runWhichFailedToMaterialize) {
  return (
    <Tag>
      <Box flex={{gap: 4}}>
        <Icon name="error_outline" color={Colors.accentRed()} />
        <AssetRunLink assetKey={asset.key} runId={runWhichFailedToMaterialize.id}>
          <TimestampDisplay
            timestamp={Number(runWhichFailedToMaterialize.endTime)}
            timeFormat={{showSeconds: false, showTimezone: false}}
          />
        </AssetRunLink>
      </Box>
    </Tag>
  );
}
```

**Data Dependencies:**

- `partitionStats` - numFailed, numMaterializing counts
- `runWhichFailedToMaterialize` - failed run details with timestamps
- `assetChecks` - check execution status and severity

### 3. Real-time Asset Health Updates

**Location:** `src/assets/_useAssetLiveDataProviderChangeSignal.cloud.tsx`

**Pattern:** Subscribes to asset health changes for live UI updates

```graphql
subscription AssetEvents {
  assetEvents(
    eventTypes: [
      ASSET_MATERIALIZATION
      ASSET_FAILED_TO_MATERIALIZE
      ASSET_HEALTH_CHANGED # Key for health status updates
      ASSET_MATERIALIZATION_PLANNED
      ASSET_OBSERVATION
    ]
  ) {
    ... on MaterializationEvent {
      assetKey {
        path
      }
      timestamp
      # Additional materialization details
    }
    ... on HealthChangedEvent {
      assetKey {
        path
      }
      # Health change details
    }
  }
}
```

### 4. Asset Check Integration

**Location:** Multiple files in `src/home/` and `src/asset-health/`

**Pattern:** Asset health integrates check execution status

```typescript
// Check failure detection
const failed = liveData.assetChecks.filter(
  (c) =>
    c.executionForLatestMaterialization?.evaluation?.severity ===
      AssetCheckSeverity.ERROR &&
    c.executionForLatestMaterialization.status ===
      AssetCheckExecutionResolvedStatus.FAILED,
);

// Check metadata access
const metadata = liveData?.assetHealth?.assetChecksStatusMetadata;
if (metadata?.__typename === "AssetHealthCheckDegradedMeta") {
  return {
    warnings: metadata.numWarningChecks,
    failures: metadata.numFailedChecks,
  };
}
```

## View-Based Data Fetching Patterns

### Health-Focused View

**Use Case:** Asset health dashboard, degraded asset lists
**Key Fields:**

- `assetHealth` with full metadata
- `partitionStats` (numFailed, numMaterializing)
- `latestMaterializationByPartition`
- `freshnessInfo` and `freshnessStatusInfo`

### Definition-Focused View

**Use Case:** Asset catalog, basic asset information
**Key Fields:**

- `assetKey`, `description`, `groupName`
- `kinds`, `metadataEntries`
- `owners`, `tags`

## Fragment Patterns for Different Data Needs

### 1. Comprehensive Health Fragment

```graphql
fragment AssetWithHealth on Asset {
  id
  key { path }
  assetHealth {
    assetHealth
    materializationStatus
    materializationStatusMetadata { ... }
    freshnessStatus
    freshnessStatusMetadata { ... }
    assetChecksStatus
    assetChecksStatusMetadata { ... }
  }
}
```

### 2. Basic Definition Fragment

```graphql
fragment AssetBasicInfo on AssetNode {
  id
  assetKey { path }
  description
  groupName
  kinds
  metadataEntries { ... }
  owners { ... }
  tags { ... }
}
```

### 3. Stateful Information Fragment

```graphql
fragment AssetStatefulInfo on AssetNode {
  latestMaterializationByPartition(partitions: [])
  freshnessInfo {
    currentLagMinutes
    currentMinutesLate
    latestMaterializationMinutesLate
  }
  freshnessPolicy {
    maximumLagMinutes
    cronSchedule
    cronScheduleTimezone
  }
  partitionStats {
    numMaterialized
    numFailed
    numMaterializing
  }
}
```

## Implementation Recommendations

### For `dg api asset` Views

**Basic View (Default):**

- Use `AssetNode` queries for definition-time data
- Include: key, description, group, kinds, metadata, owners, tags

**Status View (New):**

- Combine `Asset` and `AssetNode` data
- Include: asset health, freshness info, latest materialization, partition stats
- Follow internal app patterns for comprehensive health data

**Query Structure:**

```graphql
# Status view - comprehensive stateful data
query AssetNodesWithStatus($assetKeys: [AssetKeyInput!]!) {
  assetNodes(assetKeys: $assetKeys) {
    ...AssetBasicInfo
    ...AssetStatefulInfo
  }
  # Separate query for health data from Asset type
  assets(assetKeys: $assetKeys) {
    ...AssetWithHealth
  }
}
```

This documentation provides the foundation for implementing view-based asset APIs that match production usage patterns while exposing rich stateful information about asset materialization and freshness status.

---

## Backfills and Partitions GraphQL Patterns

### Core Backfill Types

```graphql
type PartitionBackfill {
  id: ID!
  status: BulkActionStatus!
  partitionNames: [String!]
  numPartitions: Int
  numCancelable: Int!
  fromFailure: Boolean!
  reexecutionSteps: [String!]
  assetSelection: [AssetKey!]
  partitionSetName: String
  timestamp: Float!
  endTimestamp: Float
  isAssetBackfill: Boolean!
  assetBackfillData: AssetBackfillData
  hasCancelPermission: Boolean!
  hasResumePermission: Boolean!
  user: String
  tags: [PipelineTag!]!
  title: String
  description: String
}

enum BulkActionStatus {
  REQUESTED
  COMPLETED
  FAILED
  CANCELED
  CANCELING
  COMPLETED_SUCCESS
  COMPLETED_FAILED
}

type AssetBackfillData {
  assetBackfillStatuses: [AssetBackfillStatus!]!
  rootTargetedPartitions: AssetBackfillTargetPartitions
}

type AssetBackfillTargetPartitions {
  ranges: [PartitionKeyRange!]
  partitionKeys: [String!]
}

type AssetPartitions {
  assetKey: AssetKey!
  partitions: AssetBackfillTargetPartitions
}
```

### Backfill Operations

```graphql
# Launch backfill mutation
mutation LaunchPartitionBackfill($backfillParams: LaunchBackfillParams!) {
  launchPartitionBackfill(backfillParams: $backfillParams) {
    ... on LaunchBackfillSuccess {
      backfillId
      launchedRunIds
    }
    ... on InvalidStepError {
      invalidStepKey
    }
    ... on InvalidOutputError {
      stepKey
      invalidOutputName
    }
    ... on PipelineNotFoundError {
      message
    }
    ... on RunConfigValidationInvalid {
      errors {
        message
      }
    }
    ... on PythonError {
      message
    }
  }
}

# Cancel backfill mutation
mutation CancelPartitionBackfill($backfillId: String!) {
  cancelPartitionBackfill(backfillId: $backfillId) {
    ... on CancelBackfillSuccess {
      backfillId
    }
    ... on UnauthorizedError {
      message
    }
    ... on PythonError {
      message
    }
  }
}

# Resume backfill mutation
mutation ResumePartitionBackfill($backfillId: String!) {
  resumePartitionBackfill(backfillId: $backfillId) {
    ... on ResumeBackfillSuccess {
      backfillId
    }
    ... on UnauthorizedError {
      message
    }
    ... on PythonError {
      message
    }
  }
}
```

### Backfill Policy Configuration

```graphql
type BackfillPolicy {
  maxPartitionsPerRun: Int
  description: String!
  policyType: BackfillPolicyType!
}

enum BackfillPolicyType {
  SINGLE_RUN
  MULTI_RUN
}
```

### Production Usage Patterns

**Backfill Lifecycle Management:**

1. **Launch Phase:**
   - Target partition selection (ranges or explicit keys)
   - Asset selection for asset backfills
   - Run configuration and tags
   - Backfill policy application

2. **Execution Monitoring:**
   - Status tracking across partitions
   - Progress reporting (completed/failed/in-progress)
   - Run association and monitoring
   - Error aggregation and reporting

3. **Control Operations:**
   - Cancel running backfills
   - Resume paused backfills
   - Permission-based access control

**Asset Backfill Specifics:**

```graphql
type AssetPartitionsStatusCounts {
  assetKey: AssetKey!
  numPartitionsTargeted: Int!
  numPartitionsInProgress: Int!
  numPartitionsMaterialized: Int!
  numPartitionsFailed: Int!
}

type UnpartitionedAssetStatus {
  assetKey: AssetKey!
  inProgress: Boolean!
  materialized: Boolean!
  failed: Boolean!
}
```

### Implementation Recommendations for dg CLI API

**High-Priority Backfill APIs:**

1. **`dg api backfill list`** - List active and completed backfills with filtering
2. **`dg api backfill get <backfill-id>`** - Get detailed backfill status
3. **`dg api backfill launch`** - Launch new backfills with partition targeting
4. **`dg api backfill cancel <backfill-id>`** - Cancel running backfills
5. **`dg api backfill resume <backfill-id>`** - Resume paused backfills

**Key Features:**

- Support both job backfills and asset backfills
- Partition range and explicit partition targeting
- Progress tracking with detailed status breakdowns
- Permission-aware operations
- Comprehensive error handling

**Query Patterns:**

```graphql
# List backfills with filtering
query PartitionBackfills(
  $cursor: String
  $limit: Int
  $statuses: [BulkActionStatus!]
) {
  partitionBackfillsOrError(
    cursor: $cursor
    limit: $limit
    statuses: $statuses
  ) {
    ... on PartitionBackfills {
      results {
        id
        status
        partitionSetName
        numPartitions
        timestamp
        endTimestamp
        user
        title
      }
    }
  }
}

# Get detailed backfill
query PartitionBackfill($backfillId: String!) {
  partitionBackfillOrError(backfillId: $backfillId) {
    ... on PartitionBackfill {
      id
      status
      partitionNames
      numPartitions
      numCancelable
      assetSelection {
        path
      }
      assetBackfillData {
        assetBackfillStatuses {
          ... on AssetPartitionsStatusCounts {
            assetKey {
              path
            }
            numPartitionsTargeted
            numPartitionsInProgress
            numPartitionsMaterialized
            numPartitionsFailed
          }
        }
        rootTargetedPartitions {
          ranges {
            start
            end
          }
          partitionKeys
        }
      }
      runs {
        id
        status
        startTime
        endTime
      }
    }
  }
}
```

---

## Instance and Daemon Health GraphQL Patterns

### Core Instance Type

```graphql
type Instance {
  id: ID!
  info: String
  runLauncher: RunLauncher
  runQueuingSupported: Boolean!
  runQueueConfig: RunQueueConfig
  executablePath: String!
  daemonHealth: DaemonHealth!
  hasInfo: Boolean!
  autoMaterializePaused: Boolean!
  supportsConcurrencyLimits: Boolean!
  minConcurrencyLimitValue: Int!
  maxConcurrencyLimitValue: Int!
  concurrencyLimits: [ConcurrencyKeyInfo!]!
  concurrencyLimit(concurrencyKey: String!): ConcurrencyKeyInfo!
  useAutoMaterializeSensors: Boolean!
  poolConfig: PoolConfig
  freshnessEvaluationEnabled: Boolean!
}

type RunLauncher {
  name: String!
}

type RunQueueConfig {
  maxConcurrentRuns: Int!
  tagConcurrencyLimitsYaml: String
  isOpConcurrencyAware: Boolean
}

type PoolConfig {
  poolGranularity: String
  defaultPoolLimit: Int
  opGranularityRunBuffer: Int
}
```

### Daemon Health Monitoring

```graphql
type DaemonHealth {
  id: String!
  daemonStatus(daemonType: String!): DaemonStatus!
  allDaemonStatuses: [DaemonStatus!]!
}

type DaemonStatus {
  daemonType: String!
  id: ID!
  required: Boolean!
  healthy: Boolean
  lastHeartbeatTime: Float
  lastHeartbeatErrors: [PythonError!]!
}
```

### Concurrency Management

```graphql
type ConcurrencyKeyInfo {
  concurrencyKey: String!
  slotCount: Int!
  claimedSlots: [ClaimedConcurrencySlot!]!
  pendingSteps: [PendingConcurrencyStep!]!
  activeSlotCount: Int!
  activeRunIds: [String!]!
  pendingStepCount: Int!
  pendingStepRunIds: [String!]!
  assignedStepCount: Int!
  assignedStepRunIds: [String!]!
  limit: Int
  usingDefaultLimit: Boolean
}

type ClaimedConcurrencySlot {
  runId: String!
  stepKey: String!
}

type PendingConcurrencyStep {
  runId: String!
  stepKey: String!
  enqueuedTimestamp: Float!
  assignedTimestamp: Float
  priority: Int
}
```

### Production Usage Patterns

**System Health Monitoring:**

The Instance type provides comprehensive visibility into Dagster system health and configuration:

1. **Daemon Health Tracking:**
   - Monitor all daemon processes (scheduler, sensor, backfill, etc.)
   - Track heartbeat status and error conditions
   - Identify required vs. optional daemons

2. **Run Queue Management:**
   - Monitor concurrent run limits and policies
   - Track tag-based concurrency constraints
   - Configure op-level concurrency awareness

3. **Concurrency Control:**
   - Global concurrency limit enforcement
   - Per-key slot management and queuing
   - Step-level concurrency tracking and assignment

**Key Health Indicators:**

```graphql
query InstanceHealth {
  instance {
    id
    daemonHealth {
      allDaemonStatuses {
        daemonType
        required
        healthy
        lastHeartbeatTime
        lastHeartbeatErrors {
          message
          stack
        }
      }
    }
    runQueueConfig {
      maxConcurrentRuns
      tagConcurrencyLimitsYaml
      isOpConcurrencyAware
    }
    autoMaterializePaused
    supportsConcurrencyLimits
    concurrencyLimits {
      concurrencyKey
      activeSlotCount
      pendingStepCount
      limit
    }
  }
}
```

### Implementation Recommendations for dg CLI API

**High-Priority Instance APIs:**

1. **`dg api instance status`** - Overall instance health and configuration
2. **`dg api instance daemons`** - Daemon health status and errors
3. **`dg api instance concurrency`** - Concurrency limits and queue status
4. **`dg api instance config`** - Instance configuration and capabilities

**System Monitoring Features:**

- Real-time daemon health status
- Concurrency bottleneck identification
- Queue depth and processing metrics
- Configuration validation and recommendations

**Operational Use Cases:**

1. **Health Checks:**
   - Verify all required daemons are running
   - Monitor heartbeat status and error rates
   - Detect configuration issues

2. **Performance Monitoring:**
   - Track run queue depth and processing times
   - Monitor concurrency utilization
   - Identify resource constraints

3. **Troubleshooting:**
   - Access daemon error logs and stack traces
   - Analyze concurrency bottlenecks
   - Validate configuration settings

**Query Examples:**

```graphql
# Check daemon health
query DaemonHealthStatus {
  instance {
    daemonHealth {
      allDaemonStatuses {
        daemonType
        required
        healthy
        lastHeartbeatTime
        lastHeartbeatErrors {
          message
          stack
          errorContext {
            key
            value
          }
        }
      }
    }
  }
}

# Monitor concurrency usage
query ConcurrencyStatus($concurrencyKey: String) {
  instance {
    concurrencyLimit(concurrencyKey: $concurrencyKey) {
      concurrencyKey
      slotCount
      activeSlotCount
      pendingStepCount
      claimedSlots {
        runId
        stepKey
      }
      pendingSteps {
        runId
        stepKey
        enqueuedTimestamp
        assignedTimestamp
        priority
      }
      limit
      usingDefaultLimit
    }
  }
}

# Get run queue status
query RunQueueStatus {
  instance {
    runQueuingSupported
    runQueueConfig {
      maxConcurrentRuns
      tagConcurrencyLimitsYaml
      isOpConcurrencyAware
    }
  }
}
```

### Advanced Configuration Patterns

**Pool Configuration:**

```graphql
type PoolConfig {
  poolGranularity: String # "OP" or "RUN"
  defaultPoolLimit: Int
  opGranularityRunBuffer: Int
}
```

**Auto-Materialization Control:**

```graphql
query AutoMaterializeStatus {
  instance {
    autoMaterializePaused
    useAutoMaterializeSensors
    freshnessEvaluationEnabled
  }
}
```

This provides a comprehensive foundation for system monitoring and operational control through the dg CLI API, covering both basic health checks and advanced concurrency management.

---

## Asset Checks and Evaluations GraphQL Patterns

### Core Asset Check Types

```graphql
type AssetCheck {
  name: String!
  assetKey: AssetKey!
  description: String
  job: Job
  canExecuteIndividually: Boolean!
  executions(
    cursor: String
    limit: Int
    assetKey: AssetKeyInput
  ): AssetCheckExecutionConnection!
  executionForLatestMaterialization: AssetCheckExecution
}

type AssetCheckExecution {
  id: ID!
  runId: String!
  status: AssetCheckExecutionResolvedStatus!
  timestamp: Float!
  stepKey: String
  evaluation: AssetCheckEvaluation
  targetMaterialization: MaterializationEvent
}

enum AssetCheckExecutionResolvedStatus {
  SKIPPED
  IN_PROGRESS
  SUCCEEDED
  FAILED
}

type AssetCheckEvaluation {
  severity: AssetCheckSeverity!
  passed: Boolean!
  description: String
  metadataEntries: [MetadataEntry!]!
  targetMaterialization: MaterializationEvent
}

enum AssetCheckSeverity {
  WARN
  ERROR
}
```

### Asset Condition Evaluations

```graphql
type AssetConditionEvaluationRecord {
  id: ID!
  evaluationId: Int!
  assetKey: AssetKey!
  numRequested: Int!
  timestamp: Float!
  runIds: [String!]!
  evaluation: AssetConditionEvaluation
}

type AssetConditionEvaluation {
  rootUniqueId: String!
  evaluationNodes: [AssetConditionEvaluationNode!]!
}

type AssetConditionEvaluationNode {
  uniqueId: String!
  userLabel: String
  description: String
  startTimestamp: Float
  endTimestamp: Float
  numTrue: Int!
  trueSubset: AssetSubset
  candidateSubset: AssetSubset
  childUniqueIds: [String!]!
  isPartitioned: Boolean!
}

type AssetSubset {
  subsetValue: AssetSubsetValue!
}

union AssetSubsetValue =
  | AllPartitionsAssetSubsetValue
  | PartitionKeysAssetSubsetValue
  | TimeWindowPartitionsAssetSubsetValue
```

### Auto-Materialize Asset Evaluations

```graphql
type AutoMaterializeAssetEvaluationRecord {
  id: ID!
  evaluationId: Int!
  assetKey: AssetKey!
  numRequested: Int!
  numSkipped: Int!
  numDiscarded: Int!
  timestamp: Float!
  runIds: [String!]!
  rules: [AutoMaterializeRule!]!
}

type AutoMaterializeRule {
  description: String!
  decisionType: AutoMaterializeDecisionType!
  className: String!
}

enum AutoMaterializeDecisionType {
  MATERIALIZE
  SKIP
  DISCARD
}

type AutoMaterializeAssetEvaluations {
  evaluations: [AutoMaterializeAssetEvaluationRecord!]!
}
```

### Production Usage Patterns

**Asset Check Execution Monitoring:**

Asset checks provide data quality validation with comprehensive execution tracking:

1. **Check Execution History:**
   - Per-asset check execution records
   - Integration with materialization events
   - Pass/fail status with severity levels
   - Metadata collection and reporting

2. **Quality Gate Integration:**
   - Check execution as part of materialization workflows
   - Failure handling and alerting
   - Conditional downstream execution

3. **Evaluation Results:**
   - Structured evaluation data with metadata
   - Target materialization correlation
   - Severity-based categorization (WARN vs ERROR)

**Auto-Materialization Policy Evaluation:**

```graphql
query AssetConditionEvaluations(
  $assetKey: AssetKeyInput!
  $limit: Int
  $cursor: String
) {
  assetConditionEvaluationRecordsOrError(
    assetKey: $assetKey
    limit: $limit
    cursor: $cursor
  ) {
    ... on AssetConditionEvaluationRecords {
      records {
        id
        evaluationId
        assetKey {
          path
        }
        numRequested
        timestamp
        runIds
        evaluation {
          rootUniqueId
          evaluationNodes {
            uniqueId
            userLabel
            description
            numTrue
            trueSubset {
              subsetValue {
                ... on PartitionKeysAssetSubsetValue {
                  partitionKeys
                }
                ... on TimeWindowPartitionsAssetSubsetValue {
                  timeWindows {
                    start
                    end
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Implementation Recommendations for dg CLI API

**High-Priority Asset Check APIs:**

1. **`dg api asset-check list`** - List asset checks with filtering by asset
2. **`dg api asset-check get <check-name>`** - Get check details and execution history
3. **`dg api asset-check executions`** - List check executions with status filtering
4. **`dg api asset-check execute`** - Trigger individual check execution

**High-Priority Auto-Materialize APIs:**

1. **`dg api auto-materialize evaluations`** - List evaluation records for assets
2. **`dg api auto-materialize evaluation <evaluation-id>`** - Get detailed evaluation
3. **`dg api auto-materialize rules`** - List rules and their decision impacts
4. **`dg api auto-materialize status`** - Get current auto-materialization state

**Asset Condition Evaluation APIs:**

1. **`dg api asset-condition evaluations`** - List condition evaluations
2. **`dg api asset-condition evaluation <evaluation-id>`** - Get detailed evaluation tree
3. **`dg api asset-condition partitions`** - Get true partitions for evaluation nodes

**Key Features:**

- Comprehensive data quality monitoring
- Auto-materialization policy transparency
- Evaluation history and debugging support
- Integration with asset health status
- Metadata-rich evaluation results

**Query Examples:**

```graphql
# Get asset check executions with results
query AssetCheckExecutions($assetKey: AssetKeyInput!) {
  assetChecks(assetKey: $assetKey) {
    name
    assetKey {
      path
    }
    description
    canExecuteIndividually
    executions(limit: 10) {
      results {
        id
        runId
        status
        timestamp
        evaluation {
          severity
          passed
          description
          metadataEntries {
            label
            description
            ... on TextMetadataEntry {
              text
            }
            ... on FloatMetadataEntry {
              floatValue
            }
          }
        }
        targetMaterialization {
          timestamp
          runId
        }
      }
    }
    executionForLatestMaterialization {
      status
      evaluation {
        severity
        passed
        description
      }
    }
  }
}

# Get auto-materialize evaluation details
query AutoMaterializeEvaluationDetails($evaluationId: Int!) {
  autoMaterializeAssetEvaluationsForEvaluationId(evaluationId: $evaluationId) {
    evaluations {
      id
      assetKey {
        path
      }
      numRequested
      numSkipped
      numDiscarded
      timestamp
      runIds
      rules {
        description
        decisionType
        className
      }
    }
  }
}
```

This comprehensive asset evaluation system provides essential data quality and automation insights for modern data platform operations.

---

## Resources and Configuration GraphQL Patterns

This section covers OSS resource management and configuration introspection capabilities. These APIs enable comprehensive resource discovery, configuration analysis, and dependency tracking across the entire Dagster deployment.

### Core Resource Types

```graphql
type ResourceDetails {
  id: ID!
  name: String!
  description: String
  resourceType: String!
  isTopLevel: Boolean!
  configFields: [ConfigTypeField!]!
  configuredValues: [ConfiguredValue!]!
  nestedResources: [NestedResourceEntry!]!
  parentResources: [NestedResourceEntry!]!
  assetKeysUsing: [AssetKey!]!
  jobsOpsUsing: [JobWithOps!]!
  schedulesUsing: [String!]!
  sensorsUsing: [String!]!
}

type ConfiguredValue {
  key: String!
  value: String!
  type: ConfiguredValueType!
}

enum ConfiguredValueType {
  VALUE
  ENV_VAR
}

type NestedResourceEntry {
  name: String!
  type: NestedResourceType!
  resource: ResourceDetails
}

enum NestedResourceType {
  TOP_LEVEL
  ANONYMOUS
}

type JobWithOps {
  jobName: String!
  opHandleIDs: [String!]
}
```

### Configuration Type System

```graphql
interface ConfigType {
  key: String!
  description: String
  recursiveConfigTypes: [ConfigType!]!
  typeParamKeys: [String!]!
  isSelector: Boolean!
}

type CompositeConfigType implements ConfigType {
  key: String!
  description: String
  recursiveConfigTypes: [ConfigType!]!
  typeParamKeys: [String!]!
  isSelector: Boolean!
  fields: [ConfigTypeField!]!
}

type ConfigTypeField {
  name: String!
  description: String
  configType: ConfigType!
  configTypeKey: String!
  isRequired: Boolean!
  defaultValueAsJson: String
}

type EnumConfigType implements ConfigType {
  key: String!
  description: String
  recursiveConfigTypes: [ConfigType!]!
  typeParamKeys: [String!]!
  isSelector: Boolean!
  values: [EnumConfigValue!]!
  givenName: String!
}

type EnumConfigValue {
  value: String!
  description: String
}

type ArrayConfigType implements ConfigType {
  key: String!
  description: String
  recursiveConfigTypes: [ConfigType!]!
  typeParamKeys: [String!]!
  isSelector: Boolean!
  ofType: ConfigType!
}

type MapConfigType implements ConfigType {
  key: String!
  description: String
  recursiveConfigTypes: [ConfigType!]!
  typeParamKeys: [String!]!
  isSelector: Boolean!
  keyType: ConfigType!
  valueType: ConfigType!
  keyLabelName: String
}
```

### Production Usage Patterns

**Resource Discovery and Management:**

Resource introspection provides comprehensive visibility into deployment configuration:

1. **Resource Configuration Analysis:**
   - Detailed configuration schemas and requirements
   - Environment variable usage tracking
   - Nested resource dependency mapping
   - Top-level vs. anonymous resource classification

2. **Usage Pattern Tracking:**
   - Asset-to-resource dependency mapping
   - Job and operation resource utilization
   - Schedule and sensor resource requirements
   - Cross-entity impact analysis for resource changes

3. **Configuration Validation:**
   - Type-safe configuration schema introspection
   - Required vs. optional field identification
   - Default value documentation
   - Composite and enum type support

**Configuration Schema Introspection:**

```graphql
query ResourceConfigurationDetails($selector: ResourceSelector!) {
  resourceOrError(resourceSelector: $selector) {
    ... on ResourceDetails {
      id
      name
      description
      resourceType
      isTopLevel
      configFields {
        name
        description
        configType {
          key
          description
          ... on CompositeConfigType {
            fields {
              name
              description
              isRequired
              defaultValueAsJson
              configType {
                key
                description
                ... on EnumConfigType {
                  values {
                    value
                    description
                  }
                }
              }
            }
          }
        }
        isRequired
        defaultValueAsJson
      }
      configuredValues {
        key
        value
        type # VALUE or ENV_VAR
      }
      nestedResources {
        name
        type
        resource {
          name
          resourceType
        }
      }
      parentResources {
        name
        resource {
          name
        }
      }
    }
  }
}
```

**Resource Usage and Dependency Analysis:**

```graphql
query ResourceUsageAnalysis($repositorySelector: RepositorySelector!) {
  repositoryOrError(repositorySelector: $repositorySelector) {
    ... on Repository {
      allTopLevelResourceDetails {
        name
        resourceType
        assetKeysUsing {
          path
        }
        jobsOpsUsing {
          jobName
          opHandleIDs
        }
        schedulesUsing
        sensorsUsing
        nestedResources {
          name
          type
          resource {
            name
            resourceType
            assetKeysUsing {
              path
            }
          }
        }
      }
    }
  }
}
```

### Implementation Recommendations for dg CLI API

**High-Priority Resource Management APIs:**

1. **`dg api resources list`** - List all resources with basic metadata
2. **`dg api resources get <resource-name>`** - Get detailed resource configuration
3. **`dg api resources usage <resource-name>`** - Show resource usage across entities
4. **`dg api resources config <resource-name>`** - Show configuration schema and values

**Configuration Analysis APIs:**

1. **`dg api config types`** - List configuration types in deployment
2. **`dg api config schema <resource-name>`** - Show resource configuration schema
3. **`dg api config env-vars`** - List environment variables across resources
4. **`dg api config validate`** - Validate resource configurations

**Dependency Analysis APIs:**

1. **`dg api resources dependencies <resource-name>`** - Show nested dependencies
2. **`dg api resources impact <resource-name>`** - Show usage impact analysis
3. **`dg api resources graph`** - Show resource dependency graph

**Key Features:**

- Comprehensive resource discovery and introspection
- Configuration schema validation and documentation
- Environment variable and secret usage tracking
- Cross-entity dependency analysis and impact assessment
- Type-safe configuration management

**Query Examples:**

```graphql
# Get resource configuration with nested dependencies
query ResourceConfiguration($selector: ResourceSelector!) {
  resourceOrError(resourceSelector: $selector) {
    ... on ResourceDetails {
      name
      resourceType
      configFields {
        name
        configType {
          key
          ... on CompositeConfigType {
            fields {
              name
              isRequired
              configType {
                key
                description
              }
            }
          }
        }
      }
      nestedResources {
        name
        type
        resource {
          name
          configuredValues {
            key
            value
            type
          }
        }
      }
      assetKeysUsing {
        path
      }
      jobsOpsUsing {
        jobName
        opHandleIDs
      }
    }
  }
}

# List all resources with environment variable usage
query ResourceEnvironmentVariables($repositorySelector: RepositorySelector!) {
  repositoryOrError(repositorySelector: $repositorySelector) {
    ... on Repository {
      allTopLevelResourceDetails {
        name
        resourceType
        configuredValues {
          key
          value
          type
        }
      }
    }
  }
}
```

This resource management system provides essential configuration visibility and dependency tracking for Dagster deployment maintenance and governance.

---

## Runs and Execution GraphQL Patterns

### Core Run Types

```graphql
type Run {
  id: ID!
  runId: String!
  status: RunStatus!
  pipelineName: String!
  jobName: String!
  startTime: Float
  endTime: Float
  updateTime: Float
  creationTime: Float!
  stats: RunStatsSnapshotOrError!
  stepStats: [RunStepStats!]!
  assets: [Asset!]!
  assetSelection: [AssetKey!]
  assetCheckSelection: [AssetCheckhandle!]
  canTerminate: Boolean!
  hasReExecutePermission: Boolean!
  hasTerminatePermission: Boolean!
  hasDeletePermission: Boolean!
}

enum RunStatus {
  QUEUED
  NOT_STARTED
  MANAGED
  STARTING
  STARTED
  SUCCESS
  FAILURE
  CANCELING
  CANCELED
}
```

### Production Usage Patterns

**Location:** `src/runs/RunMetricsDialog.cloud.tsx`

**Pattern:** Container metrics and resource usage tracking

```graphql
query RunContainerMetricsDialogQuery($runId: String!) {
  runContainerMetrics(runId: $runId) {
    cpuPercent {
      ...timeseriesProp
    }
    cpuUsageMs {
      ...timeseriesProp
    }
    memoryPercent {
      ...timeseriesProp
    }
    memoryUsageBytes {
      ...timeseriesProp
    }
    networkReceiveBytes {
      ...timeseriesProp
    }
    networkTransmitBytes {
      ...timeseriesProp
    }
  }
}
```

**Location:** `src/runs/RunAlertNotificationsForCountQuery.tsx`

**Pattern:** Alert integration with run notifications

```graphql
query RunAlertNotificationsForCount($runId: String!) {
  runNotificationsOrError(runId: $runId) {
    ... on RunNotifications {
      notifications {
        ... on JobRunAlertNotification {
          id
        }
        ... on AssetAlertNotification {
          id
        }
      }
    }
  }
}
```

---

## Deployments and Environment Management

### Core Deployment Types

```graphql
type DagsterCloudDeployment {
  deploymentId: ID!
  deploymentName: String!
  deploymentStatus: String!
  deploymentType: String!
  organizationId: String!
  agentType: String!
  canDeleteDeployment: Boolean!
  canHaveBranchDeployments: Boolean!
  canEditDeploymentSettings: Boolean!
  canEditDeploymentPermissions: Boolean!
  canAccessDeployment: Boolean!
  isBranchDeployment: Boolean!
  workspaceEntries: [WorkspaceEntry!]!
  parentDeployment: ParentDeployment
  branchDeploymentGitMetadata: BranchDeploymentGitMetadata
  latestCommit: GitCommit
}
```

### Production Fragment Pattern

**Location:** `src/deployment/DeploymentFragment.tsx`

**Usage:** Standard deployment information with permissions and git metadata

```graphql
fragment DeploymentFragment on DagsterCloudDeployment {
  deploymentId
  deploymentName
  deploymentStatus
  deploymentType
  organizationId
  agentType
  canDeleteDeployment
  canHaveBranchDeployments
  canEditDeploymentSettings
  canEditDeploymentPermissions
  canAccessDeployment
  isBranchDeployment
  workspaceEntries {
    locationName
    canEditCodeLocationPermissions
  }
  parentDeployment {
    deploymentId
    deploymentName
  }
  branchDeploymentGitMetadata {
    repoName
    branchName
    branchUrl
    pullRequestUrl
    pullRequestStatus
  }
  latestCommit {
    commitHash
    timestamp
    commitMessage
    commitUrl
    authorName
    authorEmail
    authorAvatarUrl
  }
}
```

## Schedules and Sensors (Automation)

### Core Schedule and Sensor Types

```graphql
type Schedule {
  id: ID!
  name: String!
  cronSchedule: String!
  pipelineRunTags: [String!]!
  scheduleState: InstigationState!
  repositoryOrigin: RepositoryOrigin!
  description: String
  partitionSet: PartitionSet
}

type Sensor {
  id: ID!
  name: String!
  sensorState: InstigationState!
  sensorType: SensorType!
  nextTick: ScheduleTick
  repositoryOrigin: RepositoryOrigin!
  description: String
}

type InstigationState {
  id: ID!
  instigationType: InstigationType!
  status: InstigationStatus!
  runningCount: Int!
  ticks(cursor: String, limit: Int): [ScheduleTick!]!
}

enum InstigationStatus {
  RUNNING
  STOPPED
  DECLARED_IN_CODE
}

enum InstigationType {
  SCHEDULE
  SENSOR
}
```

### Schedule Alert Integration

**Location:** `src/schedules/ScheduleAlertDetailsQuery.tsx`

**Pattern:** Links schedules to alert policies for monitoring automation failures

```graphql
query ScheduleAlertDetails(
  $scheduleName: String!
  $repositoryName: String!
  $repositoryLocationName: String!
) {
  alertPoliciesForSchedule(
    scheduleName: $scheduleName
    repositoryName: $repositoryName
    repositoryLocationName: $repositoryLocationName
  ) {
    id
    ...AlertPolicyFragment
  }
}
```

### Schedule and Sensor Execution Monitoring

```graphql
type ScheduleTick {
  id: ID!
  status: ScheduleTickStatus!
  timestamp: Float!
  skipReason: String
  runs: [Run!]!
  error: PythonError
  logEvents: [ScheduleTickLogEvent!]!
}

enum ScheduleTickStatus {
  STARTED
  SKIPPED
  SUCCESS
  FAILURE
}
```

### Production Usage Patterns

1. **Alert Policy Integration:** Schedules can have alert policies that monitor for execution failures
2. **Run Generation:** Both schedules and sensors create runs through their tick execution
3. **State Management:** Instigations can be RUNNING, STOPPED, or DECLARED_IN_CODE
4. **Error Handling:** Failed ticks capture error details and skip reasons
5. **Monitoring:** Tick logs provide execution history and debugging information

## Agent and Code Location Health

### Core Agent Types

```graphql
type Agent {
  id: ID!
  agentLabel: String!
  status: AgentStatus!
  lastHeartbeatTime: Float
  metadata: [AgentMetadataEntry!]!
  errors: [AgentError!]!
  codeServerStates: [CodeServerState!]!
  runWorkerStates: [RunWorkerState!]!
}

type AgentMetadataEntry {
  key: String!
  value: String!
}

type AgentError {
  timestamp: Float!
  error: PythonError!
}

enum AgentStatus {
  RUNNING
  STOPPED
  UNHEALTHY
  UNKNOWN
}
```

### Code Location Management

```graphql
type CodeServerState {
  locationName: String!
  status: CodeLocationStatus!
  error: PythonError
  startTime: Float
  lastHeartbeatTime: Float
}

type RunWorkerState {
  message: String!
  status: RunWorkerStatus!
  runId: String!
}

enum CodeLocationStatus {
  LOADING
  RUNNING
  FAILED
  STOPPED
}

enum RunWorkerStatus {
  STARTED
  RUNNING
  SUCCESS
  FAILURE
  STOPPED
}
```

### Production Agent Fragment

**Location:** `src/health/AgentFragment.tsx`

**Pattern:** Standard agent health monitoring fragment

```graphql
fragment AgentFragment on Agent {
  id
  agentLabel
  status
  lastHeartbeatTime
  metadata {
    key
    value
  }
  errors {
    timestamp
    error {
      ...CloudPythonErrorFragment
    }
  }
  codeServerStates {
    locationName
    status
    error {
      ...CloudPythonErrorFragment
    }
  }
  runWorkerStates {
    message
    status
    runId
  }
}
```

### Production Usage Patterns

1. **Health Monitoring:** Agents report heartbeat status and error states
2. **Code Location Tracking:** Each agent manages multiple code server states
3. **Run Worker Management:** Agents track run execution worker status
4. **Error Aggregation:** Agent errors are collected with timestamps for debugging
5. **Metadata Collection:** Agents report custom metadata key-value pairs
6. **Multi-tenant Support:** Single agent can serve multiple code locations

---

## Jobs and Pipelines GraphQL Patterns

### Core Job Type

```graphql
type Job implements SolidContainer & IPipelineSnapshot {
  id: ID!
  name: String!
  description: String
  solids: [Solid!]!
  modes: [Mode!]!
  pipelineSnapshotId: String!
  dagsterTypes: [DagsterType!]!
  tags: [PipelineTag!]!
  metadataEntries: [MetadataEntry!]!
  runs(cursor: String, limit: Int): [Run!]!
  schedules: [Schedule!]!
  sensors: [Sensor!]!
  graphName: String!
  runTags: [PipelineTag!]!
  isJob: Boolean!
  isAssetJob: Boolean!
  repository: Repository!
  partitionKeysOrError(
    cursor: String
    limit: Int
    reverse: Boolean
    selectedAssetKeys: [AssetKeyInput!]
  ): PartitionKeys!
  partition(
    partitionName: String!
    selectedAssetKeys: [AssetKeyInput!]
  ): PartitionTagsAndConfig
}

input JobReportingMetricsFilter {
  jobs: [QualifiedJob]
  codeLocations: [RepositoryCodeLocation]
  limit: Int
}

input QualifiedJob {
  jobName: String!
  repositoryName: String!
  repositoryLocationName: String!
}
```

### Job Usage Metrics and Reporting

**Location:** `src/settings/usage/JobLevelUsageDialog.tsx`

**Pattern:** Comprehensive job-level usage tracking across multiple metric types

```graphql
# Step duration metrics by job
query StepDurationByJobUsageMetricsQuery($startTimestamp: Float!) {
  usageMetrics {
    stepDurationByJob(startTimestamp: $startTimestamp) {
      unit
      timeGranularity
      metrics {
        startTimestamp
        endTimestamp
        value
        jobName
        repositoryLabel
        percentTotal
      }
    }
  }
}

# Credit usage metrics by job
query CreditUsageByJobMetricsQuery($startTimestamp: Float!) {
  usageMetrics {
    dagsterCreditsByJob(startTimestamp: $startTimestamp) {
      unit
      timeGranularity
      metrics {
        startTimestamp
        endTimestamp
        value
        jobName
        repositoryLabel
        percentTotal
      }
    }
  }
}

# Serverless compute metrics by job
query ServerlessUsageByJobMetricsQuery($startTimestamp: Float!) {
  usageMetrics {
    serverlessComputeMinutesByJob(startTimestamp: $startTimestamp) {
      unit
      timeGranularity
      metrics {
        startTimestamp
        endTimestamp
        value
        jobName
        repositoryLabel
        percentTotal
      }
    }
  }
}
```

### Job Insights and Performance Monitoring

**Location:** `src/insights/InsightsJobsQuery.tsx`

**Pattern:** Job performance metrics for insights dashboard

```graphql
query InsightsJobsQuery(
  $metricsFilter: JobReportingMetricsFilter
  $metricsSelector: ReportingMetricsSelector!
  $metricsStoreType: MetricsStoreType
) {
  reportingMetricsByJob(
    metricsFilter: $metricsFilter
    metricsSelector: $metricsSelector
    metricsStoreType: $metricsStoreType
  ) {
    ... on ReportingMetrics {
      metrics {
        # InsightsEntryFragment includes timing and performance data
      }
      timestamps
    }
  }
}

query InsightsJobsMetricTypesQuery {
  metricTypesForJob {
    ... on MetricTypeList {
      id
      metricTypes {
        id
        # MetricTypeFragment includes metric definitions
      }
    }
  }
}
```

### Job Alert Policy Integration

**Location:** `src/pipelines/JobSidebarAlertPoliciesTabQuery.tsx`

**Pattern:** Links jobs to alert policies for monitoring

```graphql
query JobSidebarAlertPoliciesTabQuery(
  $jobName: String!
  $locationName: String!
  $repositoryName: String!
) {
  alertPoliciesForJob(
    jobName: $jobName
    repositoryLocationName: $locationName
    repositoryName: $repositoryName
  ) {
    id
    # AlertPolicyFragment includes policy configuration
  }
}
```

### Production Usage Patterns

1. **Usage Analytics:** Jobs are tracked across multiple usage metrics (step duration, credits, serverless minutes)
2. **Performance Monitoring:** Insights system provides detailed job performance analytics
3. **Alert Integration:** Jobs can have alert policies for execution monitoring
4. **Repository Context:** Jobs are always qualified with repository and location information
5. **Asset Integration:** Jobs can be asset jobs (`isAssetJob`) linking to asset materialization
6. **Partitioning Support:** Jobs support partition-based execution and querying

### Common Fragment Pattern

```graphql
fragment MetricsByJobFragment on StepDurationUsageMetrics {
  unit
  timeGranularity
  metrics {
    startTimestamp
    endTimestamp
    value
    ... on StepDurationByJobUsageMetricValue {
      jobName
      repositoryLabel
      percentTotal
    }
    ... on CreditUsageByJobMetricValue {
      jobName
      repositoryLabel
      percentTotal
    }
  }
}
```

---

## Insights and Metrics GraphQL Patterns

### Core Reporting Types

```graphql
type ReportingMetrics {
  metrics: [ReportingEntry]!
  timestamps: [Float!]!
}

type ReportingEntry {
  entity: ReportingObjet!
  aggregateValue: Float!
  aggregateValueChange: ReportingAggregateValueChange!
  values: [Float]!
}

type ReportingAggregateValueChange {
  change: Float!
  isNewlyAvailable: Boolean!
}

union ReportingObjet =
  | ReportingAssetSelection
  | ReportingAsset
  | ReportingAssetGroup
  | ReportingJob
  | DagsterCloudDeployment

type MetricType {
  id: String!
  metricName: String!
  displayName: String!
  category: String
  unitType: ReportingUnitType
  description: String
  priority: Int
  defaultDisplayName: String!
  defaultDescription: String
  customIcon: String
  pending: Boolean
  visible: Boolean
  costMultiplier: Float
}

enum ReportingUnitType {
  INTEGER
  FLOAT
  DURATION_MS
  BYTES
}
```

### Production Fragment Patterns

**Location:** `src/insights/InsightsEntryFragment.tsx`

**Usage:** Standard reporting entry with entity polymorphism

```graphql
fragment InsightsEntryFragment on ReportingEntry {
  entity {
    ... on ReportingAssetGroup {
      groupName
      codeLocationName
      repositoryName
    }
    ... on ReportingAsset {
      assetKey { path }
      assetGroup
      codeLocationName
      repositoryName
    }
    ... on ReportingJob {
      jobName
      codeLocationName
      repositoryName
    }
    ... on DagsterCloudDeployment {
      # DeploymentFragment includes full deployment details
    }
  }
  aggregateValue
  aggregateValueChange {
    change
    isNewlyAvailable
  }
  values
}
```

**Location:** `src/insights/MetricTypeFragment.tsx`

**Usage:** Metric type definition with display configuration

```graphql
fragment MetricTypeFragment on MetricType {
  metricName
  displayName
  category
  unitType
  description
  pending
  visible
  customIcon
  costMultiplier
}
```

### Insights Query Patterns

**Multi-Entity Reporting Queries:**

```graphql
# Jobs reporting metrics
query InsightsJobsQuery(
  $metricsFilter: JobReportingMetricsFilter
  $metricsSelector: ReportingMetricsSelector!
  $metricsStoreType: MetricsStoreType
) {
  reportingMetricsByJob(
    metricsFilter: $metricsFilter
    metricsSelector: $metricsSelector
    metricsStoreType: $metricsStoreType
  ) {
    ... on ReportingMetrics {
      metrics {
        ...InsightsEntryFragment
      }
      timestamps
    }
  }
}

# Assets reporting metrics
query InsightsAssetsQuery(
  $metricsFilter: AssetReportingMetricsFilter
  $metricsSelector: ReportingMetricsSelector!
) {
  reportingMetricsByAsset(
    metricsFilter: $metricsFilter
    metricsSelector: $metricsSelector
  ) {
    ... on ReportingMetrics {
      metrics {
        ...InsightsEntryFragment
      }
      timestamps
    }
  }
}

# Deployments reporting metrics
query InsightsDeploymentsQuery(
  $metricsFilter: DeploymentReportingMetricsFilter
  $metricsSelector: ReportingMetricsSelector!
) {
  reportingMetricsByDeployment(
    metricsFilter: $metricsFilter
    metricsSelector: $metricsSelector
  ) {
    ... on ReportingMetrics {
      metrics {
        ...InsightsEntryFragment
      }
      timestamps
    }
  }
}
```

### Metric Type Discovery

```graphql
# Get available metric types for jobs
query InsightsJobsMetricTypesQuery {
  metricTypesForJob {
    ... on MetricTypeList {
      id
      metricTypes {
        id
        ...MetricTypeFragment
      }
    }
  }
}

# Get metric types for specific assets
query InsightsAssetsMetricTypesQuery(
  $timeframeSelector: ReportingMetricsTimeframeSelector!
) {
  metricTypesForAsset(timeframeSelector: $timeframeSelector) {
    ... on MetricTypeList {
      id
      metricTypes {
        id
        ...MetricTypeFragment
      }
    }
  }
}
```

### Production Usage Patterns

1. **Multi-Entity Support:** Insights work across jobs, assets, asset groups, and deployments
2. **Time Series Data:** All metrics include timestamp arrays and value arrays for charting
3. **Aggregate Calculations:** Each entry includes aggregate values and change tracking
4. **Dynamic Discovery:** Metric types are discovered dynamically per entity type
5. **Cost Integration:** Metrics can include cost multipliers for financial tracking
6. **Filtering Support:** Comprehensive filtering by code locations, repositories, and time ranges
7. **Activity Tracking:** Metrics support activity chart generation for usage patterns

### Common Use Cases

- **Performance Monitoring:** Step duration, run success rates, failure rates
- **Cost Analysis:** Credit usage, serverless compute minutes with cost multipliers
- **Activity Analysis:** Run frequency, materialization patterns
- **Trend Analysis:** Aggregate value changes over time with comparison periods

---

## Alerts & Notifications GraphQL Patterns

### Core Alert Policy Types

```graphql
type AlertPolicy {
  id: ID!
  name: String!
  description: String
  tags: [AlertPolicyTag!]!
  alertTargets: [AlertTarget!]!
  eventTypes: [AlertEventType!]!
  policyOptions: AlertPolicyOptions!
  notificationService: AlertPolicyNotification!
  enabled: Boolean!
}

type AlertPolicyTag {
  key: String!
  value: String
}

type AlertPolicyOptions {
  consecutiveFailureThreshold: Int
  includeDescriptionInNotification: Boolean
}

enum AlertEventType {
  ASSET_MATERIALIZATION_FAILED
  ASSET_MATERIALIZATION_SUCCEEDED
  ASSET_CHECK_FAILED
  ASSET_CHECK_PASSED
  JOB_RUN_FAILED
  JOB_RUN_SUCCEEDED
  SCHEDULE_SENSOR_TICK_FAILED
  SCHEDULE_SENSOR_TICK_SUCCEEDED
  CODE_LOCATION_ERROR
  AGENT_UNAVAILABLE
  INSIGHTS_THRESHOLD_BREACHED
}
```

### Alert Target Types (Polymorphic Union)

```graphql
union AlertTarget =
  | AssetGroupTarget
  | AssetKeyTarget
  | AssetSelectionTarget
  | AssetSelectionViewTarget
  | FavoritesSelectionViewTarget
  | InsightsDeploymentThresholdTarget
  | InsightsAssetGroupThresholdTarget
  | InsightsAssetThresholdTarget
  | InsightsJobThresholdTarget
  | RunResultTarget
  | LongRunningJobThresholdTarget
  | CodeLocationTarget
  | ScheduleSensorTarget

type AssetKeyTarget {
  assetKey: AssetKey!
}

type AssetGroupTarget {
  assetGroup: String!
  locationName: String!
  repoName: String!
}

type RunResultTarget {
  tags: [PipelineTag!]!
  codeLocationNames: [String!]
  jobs: [QualifiedJob!]
}

type InsightsJobThresholdTarget {
  jobName: String!
  locationName: String!
  repoName: String!
  metricName: String!
  threshold: Float!
  selectionPeriodDays: Int!
  operator: ThresholdOperator!
}

enum ThresholdOperator {
  GREATER_THAN
  LESS_THAN
  GREATER_THAN_OR_EQUAL
  LESS_THAN_OR_EQUAL
}
```

### Alert Notification Types

```graphql
union AlertPolicyNotification =
  | EmailAlertPolicyNotification
  | SlackAlertPolicyNotification
  | MicrosoftTeamsAlertPolicyNotification
  | PagerdutyAlertPolicyNotification
  | EmailOwnersAlertPolicyNotification

type EmailAlertPolicyNotification {
  emailAddresses: [String!]!
}

type SlackAlertPolicyNotification {
  slackWorkspaceName: String!
  slackChannelName: String!
}

type EmailOwnersAlertPolicyNotification {
  defaultEmailAddresses: [String!]!
}
```

### Alert Notification Records

```graphql
union AlertNotification =
  | JobRunAlertNotification
  | AssetAlertNotification
  | TickAlertNotification
  | AgentAlertNotification
  | CodeLocationAlertNotification
  | InsightsAlertNotification

type JobRunAlertNotification {
  id: ID!
  status: NotificationStatus!
  sendTimestamp: Float!
  errorMessage: String
  jobName: String!
  codeLocationName: String!
  repositoryName: String!
  eventType: AlertEventType!
  alertPolicyId: String!
  runId: String!
}

type AssetAlertNotification {
  id: ID!
  status: NotificationStatus!
  sendTimestamp: Float!
  errorMessage: String
  assetsEvents: [AssetAlertEvent!]!
  alertPolicyId: String!
  runId: String
}

type AssetAlertEvent {
  assetKey: AssetKey!
  eventType: AlertEventType!
}

enum NotificationStatus {
  SENT
  FAILED
  PENDING
}
```

### Production Usage Patterns

**Location:** `src/settings/alerts/AlertPolicyFragment.tsx`

**Pattern:** Comprehensive alert policy definition with polymorphic targets

```graphql
fragment AlertPolicyFragment on AlertPolicy {
  id
  name
  description
  tags {
    key
    value
  }
  alertTargets {
    ... on AssetKeyTarget {
      assetKey {
        path
      }
    }
    ... on RunResultTarget {
      tags {
        key
        value
      }
      codeLocationNames
      jobs {
        jobName
        codeLocationName
        repositoryName
      }
    }
    ... on InsightsJobThresholdTarget {
      jobName
      locationName
      repoName
      metricName
      threshold
      selectionPeriodDays
      operator
    }
    ... on ScheduleSensorTarget {
      codeLocationNames
      types
      schedulesSensors {
        name
        codeLocationName
        repositoryName
      }
    }
  }
  eventTypes
  policyOptions {
    consecutiveFailureThreshold
    includeDescriptionInNotification
  }
  notificationService {
    ... on EmailAlertPolicyNotification {
      emailAddresses
    }
    ... on SlackAlertPolicyNotification {
      slackWorkspaceName
      slackChannelName
    }
    ... on PagerdutyAlertPolicyNotification {
      integrationKey
    }
  }
  enabled
}
```

**Location:** `src/settings/alerts/details/AlertPolicyNotificationListQuery.tsx`

**Pattern:** Alert notification history with event context

```graphql
query AlertPolicyNotificationListQuery($alertPolicyId: String!) {
  alertPolicyNotifications(alertPolicyId: $alertPolicyId) {
    results {
      ... on JobRunAlertNotification {
        id
        status
        sendTimestamp
        errorMessage
        jobName
        codeLocationName
        repositoryName
        eventType
        alertPolicyId
        runId
      }
      ... on AssetAlertNotification {
        id
        status
        sendTimestamp
        errorMessage
        assetsEvents {
          assetKey {
            path
          }
          eventType
        }
        alertPolicyId
        runId
      }
      ... on InsightsAlertNotification {
        id
        status
        sendTimestamp
        errorMessage
        alertPolicyId
        metricName
        computedValue
      }
    }
  }
}
```

### Entity-Specific Alert Integration Patterns

1. **Job Alerts:** `src/pipelines/JobSidebarAlertPoliciesTabQuery.tsx`
   - Links jobs to alert policies for execution monitoring
   - Supports run result and long-running job threshold alerts

2. **Asset Alerts:** `src/assets/AssetAlertsSection.cloud.tsx`
   - Asset materialization and check failure alerts
   - Supports asset selection targets and favorites integration

3. **Schedule/Sensor Alerts:** `src/schedules/ScheduleAlertDetailsQuery.tsx`
   - Automation failure monitoring
   - Tick execution status alerts

4. **Code Location Alerts:** `src/code-location/CodeLocationAlertsSection.cloud.tsx`
   - Code location loading and error state monitoring
   - Agent availability alerts

### Alert Policy Management Patterns

```typescript
// Alert policy state management pattern
const { state: alertPolicy, dispatch } = useAlertPolicyReducer({
  name: "",
  description: "",
  eventTypes: [],
  targets: [],
  notificationService: null,
  enabled: true,
});

// Alert targeting with asset selection
const assetSelectionTarget = {
  __typename: "AssetSelectionTarget",
  assetSelectionString: "key_prefix:*",
};

// Insights threshold targeting
const insightsTarget = {
  __typename: "InsightsJobThresholdTarget",
  metricName: "step_duration",
  threshold: 300000, // 5 minutes in milliseconds
  selectionPeriodDays: 7,
  operator: "GREATER_THAN",
};
```

### Common Alert Query Patterns

1. **Entity-Specific Alert Policies:**

   ```graphql
   query AlertPoliciesForJob(
     $jobName: String!
     $repositoryName: String!
     $repositoryLocationName: String!
   ) {
     alertPoliciesForJob(
       jobName: $jobName
       repositoryName: $repositoryName
       repositoryLocationName: $repositoryLocationName
     ) {
       id
       ...AlertPolicyFragment
     }
   }
   ```

2. **Alert Configuration Discovery:**

   ```graphql
   query AlertConfigurationQuery {
     alertConfigurationInfo {
       slackWorkspaces {
         name
       }
       emailDomainWhitelist
       supportedNotificationServices
     }
   }
   ```

3. **Alert Notification History:**
   ```graphql
   query AlertsTriggeredByRun($runId: String!) {
     alertNotificationsForRun(runId: $runId) {
       alertPolicy {
         id
         name
       }
       notifications {
         ...JobRunAlertNotificationFragment
       }
     }
   }
   ```

---

## Teams & Users & RBAC GraphQL Patterns

### Core User Types

```graphql
type DagsterCloudUser {
  id: ID!
  userId: String!
  email: String!
  name: String!
  picture: String
  isScimProvisioned: Boolean!
}

type DagsterCloudUserWithScopedPermissionGrants {
  id: ID!
  licensedRole: String!
  user: DagsterCloudUser!
  organizationPermissionGrant: DagsterCloudScopedPermissionGrant
  deploymentPermissionGrants: [DagsterCloudScopedPermissionGrant!]!
  allBranchDeploymentsPermissionGrant: DagsterCloudScopedPermissionGrant
}

union DagsterCloudUserWithScopedPermissionGrantsOrError =
  | DagsterCloudUserWithScopedPermissionGrants
  | UnauthorizedError
  | UserNotFoundError
  | UserLimitError
  | CantRemoveAllAdminsError
  | PythonError
```

### Core Team Types

```graphql
type DagsterCloudTeam {
  id: ID!
  name: String!
  members: [DagsterCloudUser!]!
}

type DagsterCloudTeamWithScopedPermissionGrants {
  id: ID!
  team: DagsterCloudTeam!
  organizationPermissionGrant: DagsterCloudScopedPermissionGrant
  deploymentPermissionGrants: [DagsterCloudScopedPermissionGrant!]!
  allBranchDeploymentsPermissionGrant: DagsterCloudScopedPermissionGrant
}
```

### Permission Grant System

```graphql
type DagsterCloudScopedPermissionGrant {
  id: ID!
  deploymentId: String
  grant: String!
  customRoleId: String
  locationGrants: [DagsterCloudLocationPermissionGrant!]!
}

type DagsterCloudLocationPermissionGrant {
  locationName: String!
  grant: String!
  customRoleId: String
}

enum LicensedRole {
  ADMIN
  EDITOR
  LAUNCHER
  VIEWER
}

enum BuiltInGrant {
  ADMIN
  EDITOR
  LAUNCHER
  VIEWER
}
```

### Custom Role System

```graphql
type CustomRole {
  id: ID!
  name: String!
  description: String
  iconName: String
  deploymentScope: DeploymentScope!
  permissions: [String!]!
}

enum DeploymentScope {
  ALL_DEPLOYMENTS
  SINGLE_DEPLOYMENT
  ALL_BRANCH_DEPLOYMENTS
  CODE_LOCATION
}

enum Permission {
  VIEW_RUNS
  LAUNCH_RUNS
  CANCEL_RUNS
  DELETE_RUNS
  EDIT_SCHEDULES_SENSORS
  VIEW_ASSETS
  MATERIALIZE_ASSETS
  RELOAD_WORKSPACE
  WIPE_ASSETS
  VIEW_LOGS
  VIEW_COMPUTE_LOGS
  DELETE_ASSETS
}
```

### User Management Queries

```graphql
type UserCount {
  count: Int!
  userType: String!
}

type DagsterCloudUsersWithScopedPermissionGrants {
  users: [DagsterCloudUserWithScopedPermissionGrants!]!
  userCountsByHighestLevel: [UserCount!]!
}

union DagsterCloudUsersWithScopedPermissionGrantsOrError =
  | DagsterCloudUsersWithScopedPermissionGrants
  | PythonError
```

### Production Fragment Patterns

**Location:** `src/users/UserInfoFragment.tsx`

**Pattern:** Basic user information fragment

```graphql
fragment UserInfoFragment on DagsterCloudUser {
  id
  userId
  email
  name
  picture
  isScimProvisioned
}
```

**Location:** `src/users/UserPermissionRowFragment.tsx`

**Pattern:** User with comprehensive permission grants

```graphql
fragment UserPermissionRowFragment on DagsterCloudUserWithScopedPermissionGrants {
  id
  licensedRole
  user {
    ...UserInfoFragment
  }
  organizationPermissionGrant {
    id
    ...GrantFragment
  }
  deploymentPermissionGrants {
    id
    ...GrantFragment
  }
  allBranchDeploymentsPermissionGrant {
    id
    ...GrantFragment
  }
}
```

**Location:** `src/permissions/GrantFragment.tsx`

**Pattern:** Scoped permission grant with location-level overrides

```graphql
fragment GrantFragment on DagsterCloudScopedPermissionGrant {
  id
  deploymentId
  grant
  customRoleId
  locationGrants {
    locationName
    grant
    customRoleId
  }
}
```

**Location:** `src/teams/TeamInfoFragment.tsx`

**Pattern:** Team with member information

```graphql
fragment TeamInfoFragment on DagsterCloudTeam {
  id
  name
  members {
    ...UserInfoFragment
  }
}
```

**Location:** `src/roles/CustomRoleFragment.tsx`

**Pattern:** Custom role definition with permissions

```graphql
fragment CustomRoleFragment on CustomRole {
  id
  name
  description
  iconName
  deploymentScope
  permissions
}
```

### Production Usage Patterns

**Location:** `src/users/UserGrantListQuery.tsx`

**Pattern:** Comprehensive user and team permission listing

```graphql
query UserGrantListQuery {
  scimSyncEnabled
  teamPermissions {
    id
    ...TeamPermissionRowFragment
  }
  usersOrError {
    ... on DagsterCloudUsersWithScopedPermissionGrants {
      users {
        id
        ...UserPermissionRowFragment
      }
      userCountsByHighestLevel {
        count
        userType
      }
    }
  }
}
```

### RBAC Permission System

1. **Hierarchical Roles:** Licensed roles (ADMIN > EDITOR > LAUNCHER > VIEWER) determine base permissions
2. **Deployment Scoping:** Permissions can be scoped to specific deployments or all deployments
3. **Location Overrides:** Code location-specific permission grants override deployment-level grants
4. **Custom Roles:** Organization-defined roles with specific permission combinations
5. **Team-Based Access:** Teams inherit permissions and can be assigned to deployments/locations
6. **SCIM Integration:** Enterprise SSO with automated user provisioning

### Permission Grant Hierarchy

```typescript
// Permission precedence (most specific wins):
// 1. Location-level custom role
// 2. Location-level built-in grant
// 3. Deployment-level custom role
// 4. Deployment-level built-in grant
// 5. Organization-level licensed role

// Example permission evaluation
function evaluatePermission(
  user: DagsterCloudUserWithScopedPermissionGrants,
  deployment: string,
  location: string,
  permission: Permission,
): boolean {
  // Check location-level grants first
  const locationGrant = findLocationGrant(user, deployment, location);
  if (locationGrant?.customRoleId) {
    return customRoleHasPermission(locationGrant.customRoleId, permission);
  }
  if (locationGrant?.grant) {
    return builtInGrantHasPermission(locationGrant.grant, permission);
  }

  // Fall back to deployment-level grants
  const deploymentGrant = findDeploymentGrant(user, deployment);
  if (deploymentGrant?.customRoleId) {
    return customRoleHasPermission(deploymentGrant.customRoleId, permission);
  }
  if (deploymentGrant?.grant) {
    return builtInGrantHasPermission(deploymentGrant.grant, permission);
  }

  // Default to licensed role
  return licensedRoleHasPermission(user.licensedRole, permission);
}
```

### User Management Operations

1. **User Invitation:** Email-based invitation system with role assignment
2. **Permission Modification:** Granular deployment and location-level permission changes
3. **Team Management:** Team creation, member addition/removal, permission inheritance
4. **Role Assignment:** Both built-in and custom role assignment at multiple scopes
5. **SCIM Sync:** Automated user lifecycle management from identity providers
6. **Audit Logging:** Permission change tracking and compliance reporting

---

## Tokens & Authentication GraphQL Patterns

### Core Token Types

```graphql
type DagsterCloudUserToken {
  id: ID!
  token: String!
  user: DagsterCloudUser!
  createTimestamp: Float!
  revoked: Boolean!
  revokedBy: DagsterCloudUser
  revokeTimestamp: Float
  description: String
}

type DagsterCloudAgentToken {
  id: ID!
  token: String!
  createdBy: DagsterCloudUser!
  createTimestamp: Float!
  revoked: Boolean!
  revokedBy: DagsterCloudUser
  revokeTimestamp: Float
  description: String
  permissions: DagsterCloudAgentTokenPermissions!
}

type DagsterCloudAgentTokenPermissions {
  organizationPermissionGrant: DagsterCloudScopedPermissionGrant
  deploymentPermissionGrants: [DagsterCloudScopedPermissionGrant!]!
  allBranchDeploymentsPermissionGrant: DagsterCloudScopedPermissionGrant
}
```

### Token Management Operations

```graphql
union CreateUserTokenOrError = DagsterCloudUserToken | PythonError
union CreateAgentTokenOrError = DagsterCloudAgentToken | PythonError
union RevokeTokenOrError =
  | DagsterCloudUserToken
  | DagsterCloudAgentToken
  | PythonError
```

### Production Fragment Patterns

**Location:** `src/tokens/UserTokenFragment.tsx`

**Pattern:** User token with lifecycle information

```graphql
fragment UserTokenFragment on DagsterCloudUserToken {
  id
  token
  user {
    id
    userId
    email
    name
    picture
  }
  createTimestamp
  revoked
  revokedBy {
    id
    userId
    email
    name
    picture
  }
  revokeTimestamp
  description
}
```

**Location:** `src/tokens/AgentTokenFragment.tsx`

**Pattern:** Agent token with scoped permissions

```graphql
fragment AgentTokenFragment on DagsterCloudAgentToken {
  id
  token
  createdBy {
    id
    userId
    email
    name
    picture
  }
  createTimestamp
  revoked
  revokedBy {
    id
    userId
    email
    name
    picture
  }
  revokeTimestamp
  description
  permissions {
    organizationPermissionGrant {
      ...GrantFragment
    }
    deploymentPermissionGrants {
      ...GrantFragment
    }
    allBranchDeploymentsPermissionGrant {
      ...GrantFragment
    }
  }
}
```

### Authentication Patterns

1. **User Tokens:** Personal API tokens for user-level access with inherited permissions
2. **Agent Tokens:** Service tokens for Dagster agents with explicit scoped permissions
3. **Token Lifecycle:** Creation, usage tracking, revocation with audit trail
4. **Permission Inheritance:** Agent tokens use same grant system as user permissions
5. **Audit Trail:** Complete creation and revocation history with user attribution

---

## Settings & Configuration GraphQL Patterns

### Organization Settings

```graphql
type OrganizationSettings {
  allowedEmailDomains: [String!]
  scimEnabled: Boolean!
  samlEnabled: Boolean!
  enforceTeamAccess: Boolean!
  defaultDeploymentPermissions: String
  allowBranchDeployments: Boolean!
  maxSeats: Int
  billingPlan: String
}

type FeatureFlags {
  enableAdvancedScheduling: Boolean!
  enableAssetHealth: Boolean!
  enableInsights: Boolean!
  enableServerlessDeployments: Boolean!
  enableHybridDeployments: Boolean!
}
```

### Configuration Queries

```graphql
query OrganizationConfigurationQuery {
  organizationSettings {
    allowedEmailDomains
    scimEnabled
    samlEnabled
    enforceTeamAccess
    defaultDeploymentPermissions
    allowBranchDeployments
    maxSeats
    billingPlan
  }
  featureFlags {
    enableAdvancedScheduling
    enableAssetHealth
    enableInsights
    enableServerlessDeployments
    enableHybridDeployments
  }
}
```

### Settings Management

1. **SSO Configuration:** SCIM and SAML integration settings
2. **Access Control:** Email domain restrictions and team enforcement
3. **Deployment Policies:** Branch deployment permissions and defaults
4. **Feature Toggles:** Progressive feature rollout and A/B testing
5. **Billing Integration:** Plan limits and usage tracking

---

## Catalog Views & Favorites GraphQL Patterns

### Core Catalog Types

```graphql
type CatalogView {
  id: ID!
  name: String!
  description: String
  icon: String
  isPrivate: Boolean!
  creatorId: String!
  selection: AssetSelection!
}

type AssetSelection {
  querySelection: String!
}
```

### Favorites Management

```graphql
query GetUserFavoriteAssets {
  userFavoriteAssets {
    path
  }
}

mutation AddUserFavoriteAssetMutation($assetKey: AssetKeyInput!) {
  addUserFavoriteAsset(assetKey: $assetKey) {
    ... on AssetKey {
      path
    }
    ... on AssetKeyNotFoundError {
      message
    }
  }
}

mutation RemoveUserFavoriteAssetMutation($assetKey: AssetKeyInput!) {
  removeUserFavoriteAsset(assetKey: $assetKey) {
    ... on AssetKey {
      path
    }
    ... on AssetKeyNotFoundError {
      message
    }
  }
}
```

### Production Usage Patterns

**Location:** `src/catalog-view/useFavorites.tsx`

**Pattern:** Asset favorites management with bulk operations

- Individual favorite add/remove operations
- Bulk favorites management with throttling
- Real-time favorites synchronization
- Toast notifications and user feedback

### Catalog Features

1. **Personal Favorites:** User-specific asset favoriting with bulk operations
2. **Custom Views:** User-defined asset selections with query-based filtering
3. **View Sharing:** Private and public catalog view management
4. **Selection Syntax:** Advanced asset selection query language
5. **Alert Integration:** Alert policies can target catalog views and favorites

---

## Onboarding & Setup GraphQL Patterns

### Onboarding Checklist

```graphql
type OnboardingChecklist {
  id: ID!
  userId: String!
  steps: [OnboardingStep!]!
  completedSteps: [String!]!
  currentStep: String
}

type OnboardingStep {
  id: String!
  title: String!
  description: String
  type: OnboardingStepType!
  required: Boolean!
  estimatedMinutes: Int
  dependencies: [String!]!
}

enum OnboardingStepType {
  CODE_SETUP
  DEPLOYMENT_CREATION
  AGENT_INSTALLATION
  FIRST_RUN
  ASSET_MATERIALIZATION
  ALERT_CONFIGURATION
  TEAM_INVITATION
}
```

### Setup Workflow Tracking

```graphql
type SetupProgress {
  githubIntegrationComplete: Boolean!
  gitlabIntegrationComplete: Boolean!
  agentTokenCreated: Boolean!
  firstDeploymentCreated: Boolean!
  codeLocationAdded: Boolean!
  firstRunCompleted: Boolean!
}

query GetOnboardingProgress {
  onboardingChecklist {
    id
    completedSteps
    currentStep
    steps {
      id
      title
      description
      type
      required
      estimatedMinutes
      dependencies
    }
  }
  setupProgress {
    githubIntegrationComplete
    gitlabIntegrationComplete
    agentTokenCreated
    firstDeploymentCreated
    codeLocationAdded
    firstRunCompleted
  }
}
```

### Onboarding Features

1. **Progressive Disclosure:** Step-by-step guided setup process
2. **Integration Tracking:** Git provider and CI/CD integration status
3. **Milestone Recognition:** Key achievement tracking and celebration
4. **Contextual Help:** Step-specific documentation and guidance
5. **Skip Options:** Flexible workflow for experienced users

---

## Serverless & Cloud Infrastructure GraphQL Patterns

### Serverless Deployment Types

```graphql
type ServerlessDeployment {
  id: ID!
  deploymentId: String!
  region: String!
  computeConfiguration: ServerlessComputeConfig!
  containerMetrics: ContainerMetrics
  scalingPolicy: ScalingPolicy!
}

type ServerlessComputeConfig {
  cpu: String!
  memory: String!
  maxConcurrency: Int!
  timeout: Int!
  environmentVariables: [EnvironmentVariable!]!
}

type ContainerMetrics {
  cpuUtilization: Float
  memoryUtilization: Float
  requestCount: Int
  averageResponseTime: Float
  errorRate: Float
}

type ScalingPolicy {
  minInstances: Int!
  maxInstances: Int!
  targetUtilization: Float!
  scaleUpCooldown: Int!
  scaleDownCooldown: Int!
}
```

### Cloud Infrastructure Monitoring

```graphql
type CloudInfrastructure {
  provider: CloudProvider!
  region: String!
  availabilityZones: [String!]!
  networking: NetworkConfiguration!
  security: SecurityConfiguration!
}

enum CloudProvider {
  AWS
  GCP
  AZURE
}

type NetworkConfiguration {
  vpcId: String
  subnetIds: [String!]!
  securityGroupIds: [String!]!
  loadBalancerConfiguration: LoadBalancerConfig
}

type SecurityConfiguration {
  encryptionAtRest: Boolean!
  encryptionInTransit: Boolean!
  iamRoles: [IAMRole!]!
  secrets: [SecretConfiguration!]!
}
```

### Infrastructure Operations

1. **Auto-Scaling:** Dynamic resource allocation based on workload demands
2. **Multi-Region:** Geographic deployment distribution for performance
3. **Cost Optimization:** Resource usage tracking and optimization recommendations
4. **Security Compliance:** Encryption, access control, and audit logging
5. **Monitoring Integration:** Infrastructure metrics and alerting
6. **Disaster Recovery:** Backup, replication, and failover capabilities

---

## Complete dg CLI API Opportunities

### Comprehensive API Surface Analysis

Based on the complete analysis of both OSS and Plus GraphQL schemas, this section provides a comprehensive roadmap for dg CLI API expansion. The opportunities are organized by priority and implementation complexity, covering the full spectrum of Dagster operations.

### Tier 1: High-Priority OSS + Plus APIs (Immediate Implementation)

These APIs provide maximum value with relatively straightforward implementation, leveraging existing GraphQL types with clear production usage patterns.

#### Core Asset Management APIs

**OSS + Plus Available**:

```bash
# Asset lifecycle management
dg api assets list [--limit 50] [--cursor <cursor>] [--view status]
dg api assets get <asset-key> [--view status] [--include-checks] [--include-health]
dg api assets materialize <asset-key> [--partition <partition>] [--wait] [--dry-run]
dg api assets health <asset-key>  # Comprehensive health status
dg api assets lineage <asset-key> [--upstream] [--downstream] [--depth 3]

# Asset health monitoring
dg api assets health-summary [--status degraded] [--limit 20]
dg api assets freshness <asset-key>  # Freshness policies and status
dg api assets materializations <asset-key> [--limit 10] [--partition <partition>]

# Asset checks and quality
dg api asset-checks list [--asset-key <key>] [--status failed]
dg api asset-checks execute <check-name> --asset-key <key> [--wait]
dg api asset-checks history <check-name> --asset-key <key> [--limit 10]
```

**Plus-Only Extensions**:

```bash
# Advanced asset insights
dg api assets insights <asset-key>  # Usage analytics, cost tracking
dg api assets catalog-views [--user <user>] [--shared]  # Personal/shared views
dg api assets favorites [--add <asset-key>] [--remove <asset-key>]
```

#### Run and Execution Management APIs

**OSS + Plus Available**:

```bash
# Run lifecycle management
dg api runs list [--status running] [--job <job-name>] [--limit 50]
dg api runs get <run-id> [--include-logs] [--include-stats]
dg api runs launch --job <job-name> [--config <config-file>] [--tags <tags>]
dg api runs terminate <run-id> [--force] [--reason <reason>]
dg api runs delete <run-id> [--confirm]

# Execution monitoring
dg api runs status <run-id>  # Real-time status updates
dg api runs logs <run-id> [--step <step-key>] [--level error] [--follow]
dg api runs stats <run-id>  # Execution statistics and performance
dg api runs steps <run-id>  # Step-by-step execution details
```

#### Automation Control APIs

**OSS + Plus Available**:

```bash
# Schedule management
dg api schedules list [--repository <repo>] [--status running]
dg api schedules get <schedule-name> [--include-ticks] [--tick-limit 10]
dg api schedules start <schedule-name>
dg api schedules stop <schedule-name>
dg api schedules ticks <schedule-name> [--status success] [--limit 20]

# Sensor management
dg api sensors list [--repository <repo>] [--status running]
dg api sensors get <sensor-name> [--include-runs] [--run-limit 10]
dg api sensors start <sensor-name>
dg api sensors stop <sensor-name>
dg api sensors cursor <sensor-name> [--set <cursor>] [--reset]
```

#### Backfill and Partition Operations APIs

**OSS + Plus Available**:

```bash
# Partition backfills
dg api backfills list [--status in_progress] [--job <job-name>]
dg api backfills get <backfill-id> [--include-partition-status]
dg api backfills launch --job <job-name> --partitions <partitions> [--assets <assets>]
dg api backfills cancel <backfill-id> [--reason <reason>]
dg api backfills resume <backfill-id>

# Partition management
dg api partitions list --asset <asset-key> [--status missing]
dg api partitions status --asset <asset-key> --partition <partition>
dg api partitions backfill --asset <asset-key> --partitions <range>
```

#### System Health and Configuration APIs

**OSS + Plus Available**:

```bash
# Instance health monitoring
dg api instance info [--show-config] [--show-permissions]
dg api instance daemons [--daemon <type>] [--show-heartbeats]
dg api instance concurrency [--key <concurrency-key>] [--show-pending]
dg api instance runs-queue [--show-config] [--show-limits]

# Resource management
dg api resources list [--repository <repo>] [--show-usage]
dg api resources get <resource-name> [--show-config] [--show-dependencies]
dg api resources usage <resource-name>  # Cross-entity usage analysis
dg api resources env-vars [--resource <name>]  # Environment variable tracking
```

### Tier 2: Medium-Priority Specialized APIs (Phase 2 Implementation)

These APIs provide advanced functionality for specific use cases, requiring more sophisticated implementation but offering high value for power users.

#### Advanced Asset Operations

**OSS + Plus Available**:

```bash
# Auto-materialization policies
dg api assets policies list [--asset <asset-key>] [--repository <repo>]
dg api assets policies get <asset-key>  # Policy rules and evaluation history
dg api assets policies evaluate <asset-key>  # Current evaluation results
dg api assets policies debug <asset-key> --evaluation-id <id>

# Asset condition evaluations
dg api assets conditions <asset-key> [--limit 10]  # Condition evaluation history
dg api assets conditions debug <asset-key> --evaluation-id <id>  # Detailed debugging
dg api assets conditions tree <asset-key>  # Evaluation tree visualization
```

**Plus-Only Advanced Features**:

```bash
# Asset insights and analytics
dg api assets cost-analysis <asset-key> [--timeframe 30d]
dg api assets performance <asset-key> [--metric materialization_time]
dg api assets usage-patterns <asset-key> [--group-by team]
```

#### Configuration Management APIs

**OSS + Plus Available**:

```bash
# Configuration schema analysis
dg api config types [--job <job-name>] [--resource <resource-name>]
dg api config schema <resource-name>  # Detailed schema introspection
dg api config validate --file <config-file> [--strict]
dg api config export --job <job-name> [--format yaml|json]

# Environment and deployment config
dg api config deployment [--show-env-vars] [--mask-secrets]
dg api config repositories [--show-resources] [--include-nested]
```

#### Deployment and Environment Management APIs

**Plus-Only**:

```bash
# Multi-tenant deployment management
dg api deployments list [--organization <org>] [--environment <env>]
dg api deployments get <deployment-name> [--include-agents] [--include-locations]
dg api deployments status <deployment-name>  # Health and configuration status
dg api deployments promote --from <source-env> --to <target-env> [--assets <assets>]

# Code location management
dg api code-locations list [--deployment <deployment>] [--status healthy]
dg api code-locations get <location-name> [--include-repositories]
dg api code-locations reload <location-name> [--force] [--wait]
dg api code-locations logs <location-name> [--follow] [--level error]
```

### Tier 3: Advanced Plus-Only APIs (Future Enhancement)

These APIs provide sophisticated Plus-specific functionality for enterprise-grade operations, requiring significant implementation effort but offering unique value propositions.

#### Team and Access Management APIs

**Plus-Only**:

```bash
# User and team management
dg api users list [--team <team-name>] [--role <role>]
dg api users get <user-id> [--include-permissions] [--include-activity]
dg api teams list [--include-members] [--include-permissions]
dg api teams get <team-name> [--include-assets] [--include-deployments]

# Permission and access control
dg api permissions list [--user <user>] [--resource-type asset]
dg api permissions grant --user <user> --permission <permission> --resource <resource>
dg api permissions audit [--user <user>] [--timeframe 30d]
```

#### Alerts and Monitoring APIs

**Plus-Only**:

```bash
# Alert policy management
dg api alerts policies list [--type asset_failure] [--team <team>]
dg api alerts policies get <policy-id> [--include-history]
dg api alerts policies create --config <alert-config-file>
dg api alerts history [--status fired] [--policy <policy-id>] [--limit 50]

# Notification management
dg api notifications channels list [--type slack] [--team <team>]
dg api notifications test --channel <channel-id> --message <message>
dg api notifications history [--channel <channel>] [--limit 20]
```

#### Analytics and Insights APIs

**Plus-Only**:

```bash
# Usage analytics and reporting
dg api analytics usage [--timeframe 30d] [--group-by team] [--format csv]
dg api analytics costs [--deployment <deployment>] [--breakdown compute]
dg api analytics performance --metric run_duration [--percentile 95]
dg api analytics assets --metric materialization_frequency [--top 20]

# Custom reporting
dg api reports generate --template <template> [--output <file>] [--schedule]
dg api reports list [--type usage] [--creator <user>]
dg api reports export <report-id> [--format pdf|csv|json]
```

### Implementation Strategy and Prioritization

#### Phase 1: Core Operations (Months 1-3)

- **Focus**: Asset, Run, Schedule, Sensor, Backfill APIs
- **Target**: Complete OSS + basic Plus functionality
- **Value**: Covers 80% of daily operations workflows

#### Phase 2: Advanced Features (Months 4-6)

- **Focus**: Asset health, Configuration, Auto-materialization APIs
- **Target**: Advanced OSS features + Plus deployment management
- **Value**: Power user features and enterprise deployment support

#### Phase 3: Plus-Specific Features (Months 7-12)

- **Focus**: Teams, Alerts, Analytics, Advanced deployment APIs
- **Target**: Full Plus feature parity for enterprise users
- **Value**: Complete enterprise-grade platform management

### Technical Implementation Considerations

#### Unified dg CLI API Architecture

```bash
# Consistent command structure across all APIs
dg api <entity> <action> [<identifier>] [options]

# Examples:
dg api assets list --limit 50
dg api runs get abc-123 --include-logs
dg api schedules start my-schedule
dg api backfills launch --job my-job --partitions "2024-01-01:2024-01-31"
```

#### Error Handling and User Experience

- **Consistent Error Messages**: Standardized error formatting across all APIs
- **Progress Indicators**: Real-time progress for long-running operations
- **Confirmation Prompts**: Safety checks for destructive operations
- **Output Formats**: JSON, YAML, table formats for different use cases
- **Filtering and Search**: Consistent filtering patterns across list operations

#### Authentication and Authorization

- **OSS Support**: Local instance authentication and permissions
- **Plus Integration**: API token management and scoped access
- **Multi-Environment**: Context switching between deployments
- **SSO Integration**: Enterprise authentication workflows

This comprehensive API roadmap provides a complete path from basic OSS functionality to full enterprise Plus capabilities, ensuring dg CLI becomes the definitive command-line interface for all Dagster operations.

---

## Complete Implementation Roadmap and Guidance

### Executive Summary

This comprehensive analysis of Dagster's GraphQL API surface area reveals extraordinary opportunities for dg CLI expansion. With **347+ production-ready OSS GraphQL types** and **200+ Plus-specific types** analyzed, we've identified a clear path to make dg CLI the definitive command-line interface for all Dagster operations.

### Key Findings

#### OSS API Completeness

- **8 major entity groups** with complete GraphQL coverage
- **Full CRUD operations** available for all core entities (runs, assets, schedules, sensors, backfills)
- **Rich metadata integration** across all types with proper error handling
- **Production-proven stability** in OSS deployments worldwide

#### Plus API Opportunities

- **10 Plus-exclusive entity groups** providing enterprise-grade functionality
- **Advanced analytics and insights** for cost tracking, performance monitoring
- **Comprehensive team management** with RBAC and audit capabilities
- **Multi-tenant deployment management** with environment promotion workflows

#### Implementation Feasibility

- **High-value, low-complexity** opportunities in Tier 1 (80% of daily workflows)
- **Clear GraphQL patterns** with consistent query/mutation structures
- **Existing adapter layers** in dg CLI provide foundation for rapid expansion
- **Progressive implementation path** from OSS-first to Plus-complete coverage

### Strategic Implementation Roadmap

#### Phase 1: Core Operations Foundation (Q1-Q2)

**Goal**: Establish dg CLI as the primary interface for daily Dagster operations

**Scope**:

- Asset lifecycle management (list, get, materialize, health)
- Run execution control (launch, monitor, terminate, logs)
- Automation management (schedules, sensors with start/stop/status)
- Backfill operations (launch, monitor, cancel partition-based backfills)

**Expected Impact**:

- **80% coverage** of common user workflows
- **Significant CLI adoption** in OSS community
- **Foundation established** for advanced features

**Implementation Effort**: ~3-4 months, 2-3 engineers

#### Phase 2: Advanced Features (Q3-Q4)

**Goal**: Provide power-user capabilities and enterprise readiness

**Scope**:

- Asset health monitoring (comprehensive status, checks, freshness)
- Configuration management (schema introspection, validation)
- Auto-materialization debugging (policy evaluation, condition trees)
- System health monitoring (instance status, daemon health, concurrency)

**Expected Impact**:

- **Advanced troubleshooting** capabilities for data engineers
- **Configuration governance** tools for platform teams
- **Production readiness** for enterprise OSS deployments

**Implementation Effort**: ~4-5 months, 2-3 engineers

#### Phase 3: Enterprise Plus Integration (Year 2)

**Goal**: Complete Plus feature parity for enterprise customers

**Scope**:

- Multi-tenant deployment management
- Team and access control APIs
- Advanced analytics and cost tracking
- Alert policy management and notifications

**Expected Impact**:

- **Enterprise sales enablement** through CLI feature parity
- **Advanced operational workflows** for Plus customers
- **Complete platform coverage** across OSS and Plus

**Implementation Effort**: ~6-8 months, 3-4 engineers

### Technical Architecture Recommendations

#### GraphQL Adapter Pattern Enhancement

Current dg CLI architecture already provides excellent foundation:

```python
# Existing pattern in dg CLI - expand this approach
@dataclass(frozen=True)
class DgApiAssetApi:
    client: IGraphQLClient

    def list_assets(self, limit: Optional[int] = 50, cursor: Optional[str] = None, view: Optional[str] = None) -> "DgApiAssetList":
        if view == "status":
            return list_dg_plus_api_assets_with_status_via_graphql(self.client, limit=limit, cursor=cursor)
        else:
            return list_dg_plus_api_assets_via_graphql(self.client, limit=limit, cursor=cursor)
```

**Recommended Extensions**:

1. **Unified Command Structure**: `dg api <entity> <action> [<identifier>] [options]`
2. **Smart Error Handling**: GraphQL error -> user-friendly CLI messages
3. **Progressive Enhancement**: OSS-first with Plus capability detection
4. **Consistent Output Formats**: JSON, YAML, table formats across all commands

#### Priority Implementation Guidelines

##### Tier 1 Commands (Immediate Value)

Focus on highest-frequency operations with clear value propositions:

```bash
# Asset operations - highest user value
dg api assets list [--view status]           # Asset discovery
dg api assets get <asset-key> [--view status] # Asset details
dg api assets materialize <asset-key>        # Asset execution

# Run operations - core workflow
dg api runs list [--status running]         # Run monitoring
dg api runs get <run-id> [--include-logs]    # Run debugging
dg api runs launch --job <job-name>          # Run execution

# Automation control - operational necessity
dg api schedules list                        # Schedule discovery
dg api schedules start/stop <schedule-name>  # Schedule control
dg api sensors list [--status running]      # Sensor monitoring
```

##### Tier 2 Commands (Power User Features)

Advanced capabilities for sophisticated users:

```bash
# Asset health and monitoring
dg api assets health <asset-key>             # Comprehensive health status
dg api asset-checks list [--asset-key <key>] # Data quality monitoring
dg api assets policies get <asset-key>       # Auto-materialization debugging

# System administration
dg api instance daemons                      # System health monitoring
dg api resources list [--show-usage]        # Configuration management
dg api backfills launch --job <job> --partitions <range> # Bulk operations
```

##### Tier 3 Commands (Enterprise Features)

Plus-specific functionality for enterprise deployments:

```bash
# Multi-tenant management
dg api deployments list                      # Deployment overview
dg api teams get <team-name>                # Team management
dg api alerts policies list                 # Alert configuration

# Analytics and insights
dg api analytics usage [--timeframe 30d]    # Usage analytics
dg api assets cost-analysis <asset-key>     # Cost tracking
```

### Quality and Testing Strategy

#### Comprehensive Test Coverage

1. **Unit Tests**: GraphQL query/mutation correctness
2. **Integration Tests**: End-to-end CLI workflow testing
3. **Compatibility Tests**: OSS vs Plus behavior validation
4. **Performance Tests**: Large-scale GraphQL response handling

#### Documentation and Onboarding

1. **Command Reference**: Auto-generated from GraphQL schema
2. **Workflow Guides**: Common use cases and examples
3. **Migration Guides**: From dagster CLI to dg api commands
4. **Plus Feature Guides**: Enterprise-specific workflows

### Success Metrics and KPIs

#### Adoption Metrics

- **CLI Usage Growth**: Track dg api command adoption vs. Web UI usage
- **Feature Utilization**: Monitor which commands provide most value
- **User Retention**: Track continued usage patterns over time

#### Quality Metrics

- **Error Rate**: GraphQL query/mutation success rates
- **Performance**: Command execution time benchmarks
- **User Satisfaction**: Support ticket reduction, user feedback scores

#### Business Impact

- **OSS Community Growth**: Increased engagement through better tooling
- **Plus Conversion**: CLI feature parity driving enterprise adoption
- **Developer Productivity**: Workflow automation and efficiency gains

### Risk Mitigation and Contingency Planning

#### Technical Risks

- **GraphQL Schema Changes**: Version compatibility and migration strategies
- **Performance at Scale**: Large deployment response time management
- **Authentication Complexity**: Multi-environment, multi-tenant access patterns

#### Mitigation Strategies

- **Backward Compatibility**: Maintain support for older GraphQL schema versions
- **Caching and Optimization**: Intelligent query batching and response caching
- **Progressive Enhancement**: Graceful degradation when Plus features unavailable

### Conclusion and Next Steps

This comprehensive analysis demonstrates that dg CLI has unprecedented opportunity to become the definitive command-line interface for Dagster operations. With **clear implementation phases**, **well-defined technical architecture**, and **extensive GraphQL API coverage**, the path forward is both ambitious and achievable.

**Immediate Recommendations**:

1. **Prioritize Phase 1 implementation** focusing on core asset and run operations
2. **Establish consistent CLI architecture** patterns for future expansion
3. **Build comprehensive test infrastructure** to ensure quality at scale
4. **Create detailed implementation specifications** for each Tier 1 command

The convergence of robust GraphQL APIs, existing adapter infrastructure, and clear user needs creates an exceptional opportunity to deliver transformative value to the Dagster community through comprehensive CLI tooling.
