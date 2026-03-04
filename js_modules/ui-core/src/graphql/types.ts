// Generated GraphQL enums, do not edit manually.

export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & {[SubKey in K]?: Maybe<T[SubKey]>};
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & {[SubKey in K]: Maybe<T[SubKey]>};
export type MakeEmpty<T extends {[key: string]: unknown}, K extends keyof T> = {[_ in K]?: never};
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: {input: string; output: string};
  String: {input: string; output: string};
  Boolean: {input: boolean; output: boolean};
  Int: {input: number; output: number};
  Float: {input: number; output: number};
  GenericScalar: {input: any; output: any};
  JSONString: {input: any; output: any};
  RunConfigData: {input: any; output: any};
};

export type AssetBackfillPreviewParams = {
  assetSelection: Array<AssetKeyInput>;
  partitionNames: Array<Scalars['String']['input']>;
};

export enum AssetCheckCanExecuteIndividually {
  CAN_EXECUTE = 'CAN_EXECUTE',
  NEEDS_USER_CODE_UPGRADE = 'NEEDS_USER_CODE_UPGRADE',
  REQUIRES_MATERIALIZATION = 'REQUIRES_MATERIALIZATION',
}

export enum AssetCheckExecutionResolvedStatus {
  EXECUTION_FAILED = 'EXECUTION_FAILED',
  FAILED = 'FAILED',
  IN_PROGRESS = 'IN_PROGRESS',
  SKIPPED = 'SKIPPED',
  SUCCEEDED = 'SUCCEEDED',
}

export type AssetCheckHandleInput = {
  assetKey: AssetKeyInput;
  name: Scalars['String']['input'];
};

export enum AssetCheckPartitionRangeStatus {
  EXECUTION_FAILED = 'EXECUTION_FAILED',
  FAILED = 'FAILED',
  IN_PROGRESS = 'IN_PROGRESS',
  SKIPPED = 'SKIPPED',
  SUCCEEDED = 'SUCCEEDED',
}

export enum AssetCheckSeverity {
  ERROR = 'ERROR',
  WARN = 'WARN',
}

export enum AssetConditionEvaluationStatus {
  FALSE = 'FALSE',
  SKIPPED = 'SKIPPED',
  TRUE = 'TRUE',
}

export enum AssetEventHistoryEventTypeSelector {
  FAILED_TO_MATERIALIZE = 'FAILED_TO_MATERIALIZE',
  MATERIALIZATION = 'MATERIALIZATION',
  OBSERVATION = 'OBSERVATION',
}

export enum AssetEventType {
  ASSET_MATERIALIZATION = 'ASSET_MATERIALIZATION',
  ASSET_OBSERVATION = 'ASSET_OBSERVATION',
}

export type AssetGroupSelector = {
  groupName: Scalars['String']['input'];
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
};

export enum AssetHealthStatus {
  DEGRADED = 'DEGRADED',
  HEALTHY = 'HEALTHY',
  NOT_APPLICABLE = 'NOT_APPLICABLE',
  UNKNOWN = 'UNKNOWN',
  WARNING = 'WARNING',
}

export type AssetKeyInput = {
  path: Array<Scalars['String']['input']>;
};

export enum AssetMaterializationFailureReason {
  FAILED_TO_MATERIALIZE = 'FAILED_TO_MATERIALIZE',
  RUN_TERMINATED = 'RUN_TERMINATED',
  UNKNOWN = 'UNKNOWN',
  UPSTREAM_FAILED_TO_MATERIALIZE = 'UPSTREAM_FAILED_TO_MATERIALIZE',
}

export enum AssetMaterializationFailureType {
  FAILED = 'FAILED',
  SKIPPED = 'SKIPPED',
}

export enum AutoMaterializeDecisionType {
  DISCARD = 'DISCARD',
  MATERIALIZE = 'MATERIALIZE',
  SKIP = 'SKIP',
}

export enum AutoMaterializePolicyType {
  EAGER = 'EAGER',
  LAZY = 'LAZY',
}

export enum BackfillPolicyType {
  MULTI_RUN = 'MULTI_RUN',
  SINGLE_RUN = 'SINGLE_RUN',
}

export enum BulkActionStatus {
  CANCELED = 'CANCELED',
  CANCELING = 'CANCELING',
  COMPLETED = 'COMPLETED',
  COMPLETED_FAILED = 'COMPLETED_FAILED',
  COMPLETED_SUCCESS = 'COMPLETED_SUCCESS',
  FAILED = 'FAILED',
  FAILING = 'FAILING',
  REQUESTED = 'REQUESTED',
}

export type BulkActionsFilter = {
  createdAfter?: InputMaybe<Scalars['Float']['input']>;
  createdBefore?: InputMaybe<Scalars['Float']['input']>;
  statuses?: InputMaybe<Array<BulkActionStatus>>;
};

export enum ChangeReason {
  CODE_VERSION = 'CODE_VERSION',
  DEPENDENCIES = 'DEPENDENCIES',
  METADATA = 'METADATA',
  NEW = 'NEW',
  PARTITIONS_DEFINITION = 'PARTITIONS_DEFINITION',
  REMOVED = 'REMOVED',
  TAGS = 'TAGS',
}

export enum ConfiguredValueType {
  ENV_VAR = 'ENV_VAR',
  SECRET = 'SECRET',
  VALUE = 'VALUE',
}

export enum DagsterEventType {
  ALERT_FAILURE = 'ALERT_FAILURE',
  ALERT_START = 'ALERT_START',
  ALERT_SUCCESS = 'ALERT_SUCCESS',
  ASSET_CHECK_EVALUATION = 'ASSET_CHECK_EVALUATION',
  ASSET_CHECK_EVALUATION_PLANNED = 'ASSET_CHECK_EVALUATION_PLANNED',
  ASSET_FAILED_TO_MATERIALIZE = 'ASSET_FAILED_TO_MATERIALIZE',
  ASSET_HEALTH_CHANGED = 'ASSET_HEALTH_CHANGED',
  ASSET_MATERIALIZATION = 'ASSET_MATERIALIZATION',
  ASSET_MATERIALIZATION_PLANNED = 'ASSET_MATERIALIZATION_PLANNED',
  ASSET_OBSERVATION = 'ASSET_OBSERVATION',
  ASSET_STORE_OPERATION = 'ASSET_STORE_OPERATION',
  ASSET_WIPED = 'ASSET_WIPED',
  CODE_LOCATION_UPDATED = 'CODE_LOCATION_UPDATED',
  ENGINE_EVENT = 'ENGINE_EVENT',
  FRESHNESS_STATE_CHANGE = 'FRESHNESS_STATE_CHANGE',
  FRESHNESS_STATE_EVALUATION = 'FRESHNESS_STATE_EVALUATION',
  HANDLED_OUTPUT = 'HANDLED_OUTPUT',
  HOOK_COMPLETED = 'HOOK_COMPLETED',
  HOOK_ERRORED = 'HOOK_ERRORED',
  HOOK_SKIPPED = 'HOOK_SKIPPED',
  LOADED_INPUT = 'LOADED_INPUT',
  LOGS_CAPTURED = 'LOGS_CAPTURED',
  OBJECT_STORE_OPERATION = 'OBJECT_STORE_OPERATION',
  PIPELINE_CANCELED = 'PIPELINE_CANCELED',
  PIPELINE_CANCELING = 'PIPELINE_CANCELING',
  PIPELINE_DEQUEUED = 'PIPELINE_DEQUEUED',
  PIPELINE_ENQUEUED = 'PIPELINE_ENQUEUED',
  PIPELINE_FAILURE = 'PIPELINE_FAILURE',
  PIPELINE_START = 'PIPELINE_START',
  PIPELINE_STARTING = 'PIPELINE_STARTING',
  PIPELINE_SUCCESS = 'PIPELINE_SUCCESS',
  RESOURCE_INIT_FAILURE = 'RESOURCE_INIT_FAILURE',
  RESOURCE_INIT_STARTED = 'RESOURCE_INIT_STARTED',
  RESOURCE_INIT_SUCCESS = 'RESOURCE_INIT_SUCCESS',
  RUN_CANCELED = 'RUN_CANCELED',
  RUN_CANCELING = 'RUN_CANCELING',
  RUN_DEQUEUED = 'RUN_DEQUEUED',
  RUN_ENQUEUED = 'RUN_ENQUEUED',
  RUN_FAILURE = 'RUN_FAILURE',
  RUN_START = 'RUN_START',
  RUN_STARTING = 'RUN_STARTING',
  RUN_SUCCESS = 'RUN_SUCCESS',
  STEP_EXPECTATION_RESULT = 'STEP_EXPECTATION_RESULT',
  STEP_FAILURE = 'STEP_FAILURE',
  STEP_INPUT = 'STEP_INPUT',
  STEP_OUTPUT = 'STEP_OUTPUT',
  STEP_RESTARTED = 'STEP_RESTARTED',
  STEP_SKIPPED = 'STEP_SKIPPED',
  STEP_START = 'STEP_START',
  STEP_SUCCESS = 'STEP_SUCCESS',
  STEP_UP_FOR_RETRY = 'STEP_UP_FOR_RETRY',
  STEP_WORKER_STARTED = 'STEP_WORKER_STARTED',
  STEP_WORKER_STARTING = 'STEP_WORKER_STARTING',
}

export enum DefinitionsSource {
  CODE_SERVER = 'CODE_SERVER',
  CONNECTION = 'CONNECTION',
}

export enum DefsStateManagementType {
  LEGACY_CODE_SERVER_SNAPSHOTS = 'LEGACY_CODE_SERVER_SNAPSHOTS',
  LOCAL_FILESYSTEM = 'LOCAL_FILESYSTEM',
  VERSIONED_STATE_STORAGE = 'VERSIONED_STATE_STORAGE',
}

export enum DynamicPartitionsRequestType {
  ADD_PARTITIONS = 'ADD_PARTITIONS',
  DELETE_PARTITIONS = 'DELETE_PARTITIONS',
}

export enum EnvVarConsumerType {
  RESOURCE = 'RESOURCE',
}

export enum ErrorSource {
  FRAMEWORK_ERROR = 'FRAMEWORK_ERROR',
  INTERRUPT = 'INTERRUPT',
  UNEXPECTED_ERROR = 'UNEXPECTED_ERROR',
  USER_CODE_ERROR = 'USER_CODE_ERROR',
}

export enum EvaluationErrorReason {
  FIELDS_NOT_DEFINED = 'FIELDS_NOT_DEFINED',
  FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED',
  MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD',
  MISSING_REQUIRED_FIELDS = 'MISSING_REQUIRED_FIELDS',
  RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH',
  SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR',
}

export type ExecutionMetadata = {
  parentRunId?: InputMaybe<Scalars['String']['input']>;
  rootRunId?: InputMaybe<Scalars['String']['input']>;
  tags?: InputMaybe<Array<ExecutionTag>>;
};

export type ExecutionParams = {
  executionMetadata?: InputMaybe<ExecutionMetadata>;
  mode?: InputMaybe<Scalars['String']['input']>;
  preset?: InputMaybe<Scalars['String']['input']>;
  runConfigData?: InputMaybe<Scalars['RunConfigData']['input']>;
  selector: JobOrPipelineSelector;
  stepKeys?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type ExecutionTag = {
  key: Scalars['String']['input'];
  value: Scalars['String']['input'];
};

export type GraphSelector = {
  graphName: Scalars['String']['input'];
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
};

export type InstigationSelector = {
  name: Scalars['String']['input'];
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
};

export enum InstigationStatus {
  RUNNING = 'RUNNING',
  STOPPED = 'STOPPED',
}

export enum InstigationTickStatus {
  FAILURE = 'FAILURE',
  SKIPPED = 'SKIPPED',
  STARTED = 'STARTED',
  SUCCESS = 'SUCCESS',
}

export enum InstigationType {
  AUTO_MATERIALIZE = 'AUTO_MATERIALIZE',
  SCHEDULE = 'SCHEDULE',
  SENSOR = 'SENSOR',
}

export type JobOrPipelineSelector = {
  assetCheckSelection?: InputMaybe<Array<AssetCheckHandleInput>>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  jobName?: InputMaybe<Scalars['String']['input']>;
  pipelineName?: InputMaybe<Scalars['String']['input']>;
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  solidSelection?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type LaunchBackfillParams = {
  allPartitions?: InputMaybe<Scalars['Boolean']['input']>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  description?: InputMaybe<Scalars['String']['input']>;
  forceSynchronousSubmission?: InputMaybe<Scalars['Boolean']['input']>;
  fromFailure?: InputMaybe<Scalars['Boolean']['input']>;
  partitionNames?: InputMaybe<Array<Scalars['String']['input']>>;
  partitionsByAssets?: InputMaybe<Array<InputMaybe<PartitionsByAssetSelector>>>;
  reexecutionSteps?: InputMaybe<Array<Scalars['String']['input']>>;
  runConfigData?: InputMaybe<Scalars['RunConfigData']['input']>;
  selector?: InputMaybe<PartitionSetSelector>;
  tags?: InputMaybe<Array<ExecutionTag>>;
  title?: InputMaybe<Scalars['String']['input']>;
};

export enum LocationStateChangeEventType {
  LOCATION_DISCONNECTED = 'LOCATION_DISCONNECTED',
  LOCATION_ERROR = 'LOCATION_ERROR',
  LOCATION_RECONNECTED = 'LOCATION_RECONNECTED',
  LOCATION_UPDATED = 'LOCATION_UPDATED',
}

export enum LogLevel {
  CRITICAL = 'CRITICAL',
  DEBUG = 'DEBUG',
  ERROR = 'ERROR',
  INFO = 'INFO',
  WARNING = 'WARNING',
}

export type MarshalledInput = {
  inputName: Scalars['String']['input'];
  key: Scalars['String']['input'];
};

export type MarshalledOutput = {
  key: Scalars['String']['input'];
  outputName: Scalars['String']['input'];
};

export enum NestedResourceType {
  ANONYMOUS = 'ANONYMOUS',
  TOP_LEVEL = 'TOP_LEVEL',
}

export enum ObjectStoreOperationType {
  CP_OBJECT = 'CP_OBJECT',
  GET_OBJECT = 'GET_OBJECT',
  RM_OBJECT = 'RM_OBJECT',
  SET_OBJECT = 'SET_OBJECT',
}

export enum PartitionDefinitionType {
  DYNAMIC = 'DYNAMIC',
  MULTIPARTITIONED = 'MULTIPARTITIONED',
  STATIC = 'STATIC',
  TIME_WINDOW = 'TIME_WINDOW',
}

export type PartitionRangeSelector = {
  end: Scalars['String']['input'];
  start: Scalars['String']['input'];
};

export enum PartitionRangeStatus {
  FAILED = 'FAILED',
  MATERIALIZED = 'MATERIALIZED',
  MATERIALIZING = 'MATERIALIZING',
}

export type PartitionSetSelector = {
  partitionSetName: Scalars['String']['input'];
  repositorySelector: RepositorySelector;
};

export type PartitionsByAssetSelector = {
  assetKey: AssetKeyInput;
  partitions?: InputMaybe<PartitionsSelector>;
};

export type PartitionsSelector = {
  range?: InputMaybe<PartitionRangeSelector>;
  ranges?: InputMaybe<Array<PartitionRangeSelector>>;
};

export type PipelineSelector = {
  assetCheckSelection?: InputMaybe<Array<AssetCheckHandleInput>>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  pipelineName: Scalars['String']['input'];
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  solidSelection?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type ReexecutionParams = {
  extraTags?: InputMaybe<Array<ExecutionTag>>;
  parentRunId: Scalars['String']['input'];
  strategy: ReexecutionStrategy;
  useParentRunTags?: InputMaybe<Scalars['Boolean']['input']>;
};

export enum ReexecutionStrategy {
  ALL_STEPS = 'ALL_STEPS',
  FROM_ASSET_FAILURE = 'FROM_ASSET_FAILURE',
  FROM_FAILURE = 'FROM_FAILURE',
}

export type ReportAssetCheckEvaluationParams = {
  assetKey: AssetKeyInput;
  checkName: Scalars['String']['input'];
  partition?: InputMaybe<Scalars['String']['input']>;
  passed: Scalars['Boolean']['input'];
  serializedMetadata?: InputMaybe<Scalars['String']['input']>;
  severity?: InputMaybe<AssetCheckSeverity>;
};

export type ReportRunlessAssetEventsParams = {
  assetKey: AssetKeyInput;
  description?: InputMaybe<Scalars['String']['input']>;
  eventType: AssetEventType;
  partitionKeys?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export enum RepositoryLocationLoadStatus {
  LOADED = 'LOADED',
  LOADING = 'LOADING',
}

export type RepositorySelector = {
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
};

export type ResourceSelector = {
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  resourceName: Scalars['String']['input'];
};

export enum RunStatus {
  CANCELED = 'CANCELED',
  CANCELING = 'CANCELING',
  FAILURE = 'FAILURE',
  MANAGED = 'MANAGED',
  NOT_STARTED = 'NOT_STARTED',
  QUEUED = 'QUEUED',
  STARTED = 'STARTED',
  STARTING = 'STARTING',
  SUCCESS = 'SUCCESS',
}

export enum RunsFeedView {
  BACKFILLS = 'BACKFILLS',
  ROOTS = 'ROOTS',
  RUNS = 'RUNS',
}

export type RunsFilter = {
  createdAfter?: InputMaybe<Scalars['Float']['input']>;
  createdBefore?: InputMaybe<Scalars['Float']['input']>;
  mode?: InputMaybe<Scalars['String']['input']>;
  pipelineName?: InputMaybe<Scalars['String']['input']>;
  runIds?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  snapshotId?: InputMaybe<Scalars['String']['input']>;
  statuses?: InputMaybe<Array<RunStatus>>;
  tags?: InputMaybe<Array<ExecutionTag>>;
  updatedAfter?: InputMaybe<Scalars['Float']['input']>;
  updatedBefore?: InputMaybe<Scalars['Float']['input']>;
};

export type ScheduleSelector = {
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  scheduleName: Scalars['String']['input'];
};

export enum ScheduleStatus {
  ENDED = 'ENDED',
  RUNNING = 'RUNNING',
  STOPPED = 'STOPPED',
}

export type SensorSelector = {
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  sensorName: Scalars['String']['input'];
};

export enum SensorType {
  ASSET = 'ASSET',
  AUTOMATION = 'AUTOMATION',
  AUTO_MATERIALIZE = 'AUTO_MATERIALIZE',
  FRESHNESS_POLICY = 'FRESHNESS_POLICY',
  MULTI_ASSET = 'MULTI_ASSET',
  RUN_STATUS = 'RUN_STATUS',
  STANDARD = 'STANDARD',
  UNKNOWN = 'UNKNOWN',
}

export enum StaleCauseCategory {
  CODE = 'CODE',
  DATA = 'DATA',
  DEPENDENCIES = 'DEPENDENCIES',
}

export enum StaleStatus {
  FRESH = 'FRESH',
  MISSING = 'MISSING',
  STALE = 'STALE',
}

export enum StepEventStatus {
  FAILURE = 'FAILURE',
  IN_PROGRESS = 'IN_PROGRESS',
  SKIPPED = 'SKIPPED',
  SUCCESS = 'SUCCESS',
}

export type StepExecution = {
  marshalledInputs?: InputMaybe<Array<MarshalledInput>>;
  marshalledOutputs?: InputMaybe<Array<MarshalledOutput>>;
  stepKey: Scalars['String']['input'];
};

export enum StepKind {
  COMPUTE = 'COMPUTE',
  UNRESOLVED_COLLECT = 'UNRESOLVED_COLLECT',
  UNRESOLVED_MAPPED = 'UNRESOLVED_MAPPED',
}

export type StepOutputHandle = {
  outputName: Scalars['String']['input'];
  stepKey: Scalars['String']['input'];
};

export type TagInput = {
  key: Scalars['String']['input'];
  value: Scalars['String']['input'];
};

export enum TerminateRunPolicy {
  MARK_AS_CANCELED_IMMEDIATELY = 'MARK_AS_CANCELED_IMMEDIATELY',
  SAFE_TERMINATE = 'SAFE_TERMINATE',
}
