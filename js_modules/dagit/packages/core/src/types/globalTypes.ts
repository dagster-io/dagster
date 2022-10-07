/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum AssetComputeStatus {
  NONE = 'NONE',
  OUT_OF_DATE = 'OUT_OF_DATE',
  UP_TO_DATE = 'UP_TO_DATE',
}

export enum BackfillStatus {
  CANCELED = 'CANCELED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  INCOMPLETE = 'INCOMPLETE',
  IN_PROGRESS = 'IN_PROGRESS',
  REQUESTED = 'REQUESTED',
}

export enum BulkActionStatus {
  CANCELED = 'CANCELED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  REQUESTED = 'REQUESTED',
}

export enum ComputeIOType {
  STDERR = 'STDERR',
  STDOUT = 'STDOUT',
}

export enum DagsterEventType {
  ALERT_FAILURE = 'ALERT_FAILURE',
  ALERT_START = 'ALERT_START',
  ALERT_SUCCESS = 'ALERT_SUCCESS',
  ASSET_MATERIALIZATION = 'ASSET_MATERIALIZATION',
  ASSET_MATERIALIZATION_PLANNED = 'ASSET_MATERIALIZATION_PLANNED',
  ASSET_OBSERVATION = 'ASSET_OBSERVATION',
  ASSET_STORE_OPERATION = 'ASSET_STORE_OPERATION',
  ENGINE_EVENT = 'ENGINE_EVENT',
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
  SCHEDULE = 'SCHEDULE',
  SENSOR = 'SENSOR',
}

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

export enum ObjectStoreOperationType {
  CP_OBJECT = 'CP_OBJECT',
  GET_OBJECT = 'GET_OBJECT',
  RM_OBJECT = 'RM_OBJECT',
  SET_OBJECT = 'SET_OBJECT',
}

export enum ReexecutionStrategy {
  ALL_STEPS = 'ALL_STEPS',
  FROM_FAILURE = 'FROM_FAILURE',
}

export enum RepositoryLocationLoadStatus {
  LOADED = 'LOADED',
  LOADING = 'LOADING',
}

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

export enum StepEventStatus {
  FAILURE = 'FAILURE',
  IN_PROGRESS = 'IN_PROGRESS',
  SKIPPED = 'SKIPPED',
  SUCCESS = 'SUCCESS',
}

export enum StepKind {
  COMPUTE = 'COMPUTE',
  UNRESOLVED_COLLECT = 'UNRESOLVED_COLLECT',
  UNRESOLVED_MAPPED = 'UNRESOLVED_MAPPED',
}

export enum TerminateRunPolicy {
  MARK_AS_CANCELED_IMMEDIATELY = 'MARK_AS_CANCELED_IMMEDIATELY',
  SAFE_TERMINATE = 'SAFE_TERMINATE',
}

export interface AssetGroupSelector {
  groupName: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetKeyInput {
  path: string[];
}

export interface ExecutionMetadata {
  runId?: string | null;
  tags?: ExecutionTag[] | null;
  rootRunId?: string | null;
  parentRunId?: string | null;
}

export interface ExecutionParams {
  selector: JobOrPipelineSelector;
  runConfigData?: any | null;
  mode?: string | null;
  executionMetadata?: ExecutionMetadata | null;
  stepKeys?: string[] | null;
  preset?: string | null;
}

export interface ExecutionTag {
  key: string;
  value: string;
}

export interface GraphSelector {
  graphName: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface InstigationSelector {
  repositoryName: string;
  repositoryLocationName: string;
  name: string;
}

export interface JobOrPipelineSelector {
  pipelineName?: string | null;
  jobName?: string | null;
  repositoryName: string;
  repositoryLocationName: string;
  solidSelection?: string[] | null;
  assetSelection?: AssetKeyInput[] | null;
}

export interface LaunchBackfillParams {
  selector: PartitionSetSelector;
  partitionNames?: string[] | null;
  reexecutionSteps?: string[] | null;
  assetSelection?: AssetKeyInput[] | null;
  fromFailure?: boolean | null;
  allPartitions?: boolean | null;
  tags?: ExecutionTag[] | null;
  forceSynchronousSubmission?: boolean | null;
}

export interface PartitionSetSelector {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
}

export interface PipelineSelector {
  pipelineName: string;
  repositoryName: string;
  repositoryLocationName: string;
  solidSelection?: string[] | null;
  assetSelection?: AssetKeyInput[] | null;
}

export interface ReexecutionParams {
  parentRunId: string;
  strategy: ReexecutionStrategy;
}

export interface RepositorySelector {
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunsFilter {
  runIds?: (string | null)[] | null;
  pipelineName?: string | null;
  tags?: ExecutionTag[] | null;
  statuses?: RunStatus[] | null;
  snapshotId?: string | null;
  updatedAfter?: number | null;
  createdBefore?: number | null;
  mode?: string | null;
}

export interface ScheduleSelector {
  repositoryName: string;
  repositoryLocationName: string;
  scheduleName: string;
}

export interface SensorSelector {
  repositoryName: string;
  repositoryLocationName: string;
  sensorName: string;
}

//==============================================================
// END Enums and Input Objects
//==============================================================
