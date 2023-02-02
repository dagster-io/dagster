// Generated GraphQL types, do not edit manually.

export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & {[SubKey in K]?: Maybe<T[SubKey]>};
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & {[SubKey in K]: Maybe<T[SubKey]>};
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: string;
  String: string;
  Boolean: boolean;
  Int: number;
  Float: number;
  Cursor: any;
  GenericScalar: any;
  RunConfigData: any;
};

export type AlertFailureEvent = MessageEvent &
  RunEvent & {
    __typename: 'AlertFailureEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type AlertStartEvent = MessageEvent &
  RunEvent & {
    __typename: 'AlertStartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type AlertSuccessEvent = MessageEvent &
  RunEvent & {
    __typename: 'AlertSuccessEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ArrayConfigType = ConfigType &
  WrappingConfigType & {
    __typename: 'ArrayConfigType';
    description: Maybe<Scalars['String']>;
    isSelector: Scalars['Boolean'];
    key: Scalars['String'];
    ofType: ConfigType;
    recursiveConfigTypes: Array<ConfigType>;
    typeParamKeys: Array<Scalars['String']>;
  };

export type Asset = {
  __typename: 'Asset';
  assetMaterializations: Array<MaterializationEvent>;
  assetObservations: Array<ObservationEvent>;
  definition: Maybe<AssetNode>;
  id: Scalars['String'];
  key: AssetKey;
};

export type AssetAssetMaterializationsArgs = {
  afterTimestampMillis?: InputMaybe<Scalars['String']>;
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitionInLast?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
  tags?: InputMaybe<Array<InputTag>>;
};

export type AssetAssetObservationsArgs = {
  afterTimestampMillis?: InputMaybe<Scalars['String']>;
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitionInLast?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
};

export type AssetConnection = {
  __typename: 'AssetConnection';
  nodes: Array<Asset>;
};

export type AssetDependency = {
  __typename: 'AssetDependency';
  asset: AssetNode;
  inputName: Scalars['String'];
};

export type AssetFreshnessInfo = {
  __typename: 'AssetFreshnessInfo';
  currentMinutesLate: Maybe<Scalars['Float']>;
  latestMaterializationMinutesLate: Maybe<Scalars['Float']>;
};

export type AssetGroup = {
  __typename: 'AssetGroup';
  assetKeys: Array<AssetKey>;
  groupName: Scalars['String'];
};

export type AssetGroupSelector = {
  groupName: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type AssetKey = {
  __typename: 'AssetKey';
  path: Array<Scalars['String']>;
};

export type AssetKeyInput = {
  path: Array<Scalars['String']>;
};

export type AssetLatestInfo = {
  __typename: 'AssetLatestInfo';
  assetKey: AssetKey;
  inProgressRunIds: Array<Scalars['String']>;
  latestMaterialization: Maybe<MaterializationEvent>;
  latestRun: Maybe<Run>;
  unstartedRunIds: Array<Scalars['String']>;
};

export type AssetLineageInfo = {
  __typename: 'AssetLineageInfo';
  assetKey: AssetKey;
  partitions: Array<Scalars['String']>;
};

export type AssetMaterializationPlannedEvent = MessageEvent &
  RunEvent & {
    __typename: 'AssetMaterializationPlannedEvent';
    assetKey: Maybe<AssetKey>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type AssetMetadataEntry = MetadataEntry & {
  __typename: 'AssetMetadataEntry';
  assetKey: AssetKey;
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
};

export type AssetNode = {
  __typename: 'AssetNode';
  assetKey: AssetKey;
  assetMaterializationUsedData: Array<MaterializationUpstreamDataVersion>;
  assetMaterializations: Array<MaterializationEvent>;
  assetObservations: Array<ObservationEvent>;
  computeKind: Maybe<Scalars['String']>;
  configField: Maybe<ConfigTypeField>;
  currentLogicalVersion: Maybe<Scalars['String']>;
  dependedBy: Array<AssetDependency>;
  dependedByKeys: Array<AssetKey>;
  dependencies: Array<AssetDependency>;
  dependencyKeys: Array<AssetKey>;
  description: Maybe<Scalars['String']>;
  freshnessInfo: Maybe<AssetFreshnessInfo>;
  freshnessPolicy: Maybe<FreshnessPolicy>;
  graphName: Maybe<Scalars['String']>;
  groupName: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  isObservable: Scalars['Boolean'];
  isPartitioned: Scalars['Boolean'];
  isSource: Scalars['Boolean'];
  jobNames: Array<Scalars['String']>;
  jobs: Array<Pipeline>;
  latestMaterializationByPartition: Array<Maybe<MaterializationEvent>>;
  materializedPartitions: MaterializedPartitions;
  metadataEntries: Array<MetadataEntry>;
  op: Maybe<SolidDefinition>;
  opName: Maybe<Scalars['String']>;
  opNames: Array<Scalars['String']>;
  opVersion: Maybe<Scalars['String']>;
  partitionDefinition: Maybe<PartitionDefinition>;
  partitionKeys: Array<Scalars['String']>;
  partitionKeysByDimension: Array<DimensionPartitionKeys>;
  partitionStats: Maybe<PartitionStats>;
  projectedLogicalVersion: Maybe<Scalars['String']>;
  repository: Repository;
  requiredResources: Array<ResourceRequirement>;
  type: Maybe<DagsterType>;
};

export type AssetNodeAssetMaterializationUsedDataArgs = {
  timestampMillis: Scalars['String'];
};

export type AssetNodeAssetMaterializationsArgs = {
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
};

export type AssetNodeAssetObservationsArgs = {
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
};

export type AssetNodeLatestMaterializationByPartitionArgs = {
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
};

export type AssetNodePartitionKeysByDimensionArgs = {
  endIdx?: InputMaybe<Scalars['Int']>;
  startIdx?: InputMaybe<Scalars['Int']>;
};

export type AssetNodeDefinitionCollision = {
  __typename: 'AssetNodeDefinitionCollision';
  assetKey: AssetKey;
  repositories: Array<Repository>;
};

export type AssetNodeOrError = AssetNode | AssetNotFoundError;

export type AssetNotFoundError = Error & {
  __typename: 'AssetNotFoundError';
  message: Scalars['String'];
};

export type AssetOrError = Asset | AssetNotFoundError;

export type AssetWipeMutationResult =
  | AssetNotFoundError
  | AssetWipeSuccess
  | PythonError
  | UnauthorizedError;

export type AssetWipeSuccess = {
  __typename: 'AssetWipeSuccess';
  assetKeys: Array<AssetKey>;
};

export type AssetsOrError = AssetConnection | PythonError;

export type BoolMetadataEntry = MetadataEntry & {
  __typename: 'BoolMetadataEntry';
  boolValue: Maybe<Scalars['Boolean']>;
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
};

export enum BulkActionStatus {
  CANCELED = 'CANCELED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  REQUESTED = 'REQUESTED',
}

export type CancelBackfillResult = CancelBackfillSuccess | PythonError | UnauthorizedError;

export type CancelBackfillSuccess = {
  __typename: 'CancelBackfillSuccess';
  backfillId: Scalars['String'];
};

export type CapturedLogs = {
  __typename: 'CapturedLogs';
  cursor: Maybe<Scalars['String']>;
  logKey: Array<Scalars['String']>;
  stderr: Maybe<Scalars['String']>;
  stdout: Maybe<Scalars['String']>;
};

export type CapturedLogsMetadata = {
  __typename: 'CapturedLogsMetadata';
  stderrDownloadUrl: Maybe<Scalars['String']>;
  stderrLocation: Maybe<Scalars['String']>;
  stdoutDownloadUrl: Maybe<Scalars['String']>;
  stdoutLocation: Maybe<Scalars['String']>;
};

export type CompositeConfigType = ConfigType & {
  __typename: 'CompositeConfigType';
  description: Maybe<Scalars['String']>;
  fields: Array<ConfigTypeField>;
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
};

export type CompositeSolidDefinition = ISolidDefinition &
  SolidContainer & {
    __typename: 'CompositeSolidDefinition';
    assetNodes: Array<AssetNode>;
    description: Maybe<Scalars['String']>;
    id: Scalars['ID'];
    inputDefinitions: Array<InputDefinition>;
    inputMappings: Array<InputMapping>;
    metadata: Array<MetadataItemDefinition>;
    modes: Array<Mode>;
    name: Scalars['String'];
    outputDefinitions: Array<OutputDefinition>;
    outputMappings: Array<OutputMapping>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
  };

export type CompositeSolidDefinitionSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type CompositeSolidDefinitionSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export enum ComputeIoType {
  STDERR = 'STDERR',
  STDOUT = 'STDOUT',
}

export type ComputeLogFile = {
  __typename: 'ComputeLogFile';
  cursor: Scalars['Int'];
  data: Maybe<Scalars['String']>;
  downloadUrl: Maybe<Scalars['String']>;
  path: Scalars['String'];
  size: Scalars['Int'];
};

export type ComputeLogs = {
  __typename: 'ComputeLogs';
  runId: Scalars['String'];
  stderr: Maybe<ComputeLogFile>;
  stdout: Maybe<ComputeLogFile>;
  stepKey: Scalars['String'];
};

export type ConfigType = {
  description: Maybe<Scalars['String']>;
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
};

export type ConfigTypeField = {
  __typename: 'ConfigTypeField';
  configType: ConfigType;
  configTypeKey: Scalars['String'];
  defaultValueAsJson: Maybe<Scalars['String']>;
  description: Maybe<Scalars['String']>;
  isRequired: Scalars['Boolean'];
  name: Scalars['String'];
};

export type ConfigTypeNotFoundError = Error & {
  __typename: 'ConfigTypeNotFoundError';
  configTypeName: Scalars['String'];
  message: Scalars['String'];
  pipeline: Pipeline;
};

export type ConfigTypeOrError =
  | CompositeConfigType
  | ConfigTypeNotFoundError
  | EnumConfigType
  | PipelineNotFoundError
  | PythonError
  | RegularConfigType;

export type ConflictingExecutionParamsError = Error & {
  __typename: 'ConflictingExecutionParamsError';
  message: Scalars['String'];
};

export type DaemonHealth = {
  __typename: 'DaemonHealth';
  allDaemonStatuses: Array<DaemonStatus>;
  daemonStatus: DaemonStatus;
  id: Scalars['String'];
};

export type DaemonHealthDaemonStatusArgs = {
  daemonType?: InputMaybe<Scalars['String']>;
};

export type DaemonStatus = {
  __typename: 'DaemonStatus';
  daemonType: Scalars['String'];
  healthy: Maybe<Scalars['Boolean']>;
  id: Scalars['ID'];
  lastHeartbeatErrors: Array<PythonError>;
  lastHeartbeatTime: Maybe<Scalars['Float']>;
  required: Scalars['Boolean'];
};

export type DagitMutation = {
  __typename: 'DagitMutation';
  cancelPartitionBackfill: CancelBackfillResult;
  deletePipelineRun: DeletePipelineRunResult;
  deleteRun: DeletePipelineRunResult;
  launchPartitionBackfill: LaunchBackfillResult;
  launchPipelineExecution: LaunchRunResult;
  launchPipelineReexecution: LaunchRunReexecutionResult;
  launchRun: LaunchRunResult;
  launchRunReexecution: LaunchRunReexecutionResult;
  logTelemetry: LogTelemetryMutationResult;
  reloadRepositoryLocation: ReloadRepositoryLocationMutationResult;
  reloadWorkspace: ReloadWorkspaceMutationResult;
  resumePartitionBackfill: ResumeBackfillResult;
  setNuxSeen: Scalars['Boolean'];
  setSensorCursor: SensorOrError;
  shutdownRepositoryLocation: ShutdownRepositoryLocationMutationResult;
  startSchedule: ScheduleMutationResult;
  startSensor: SensorOrError;
  stopRunningSchedule: ScheduleMutationResult;
  stopSensor: StopSensorMutationResultOrError;
  terminatePipelineExecution: TerminateRunResult;
  terminateRun: TerminateRunResult;
  wipeAssets: AssetWipeMutationResult;
};

export type DagitMutationCancelPartitionBackfillArgs = {
  backfillId: Scalars['String'];
};

export type DagitMutationDeletePipelineRunArgs = {
  runId: Scalars['String'];
};

export type DagitMutationDeleteRunArgs = {
  runId: Scalars['String'];
};

export type DagitMutationLaunchPartitionBackfillArgs = {
  backfillParams: LaunchBackfillParams;
};

export type DagitMutationLaunchPipelineExecutionArgs = {
  executionParams: ExecutionParams;
};

export type DagitMutationLaunchPipelineReexecutionArgs = {
  executionParams?: InputMaybe<ExecutionParams>;
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

export type DagitMutationLaunchRunArgs = {
  executionParams: ExecutionParams;
};

export type DagitMutationLaunchRunReexecutionArgs = {
  executionParams?: InputMaybe<ExecutionParams>;
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

export type DagitMutationLogTelemetryArgs = {
  action: Scalars['String'];
  clientId: Scalars['String'];
  clientTime: Scalars['String'];
  metadata: Scalars['String'];
};

export type DagitMutationReloadRepositoryLocationArgs = {
  repositoryLocationName: Scalars['String'];
};

export type DagitMutationResumePartitionBackfillArgs = {
  backfillId: Scalars['String'];
};

export type DagitMutationSetSensorCursorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  sensorSelector: SensorSelector;
};

export type DagitMutationShutdownRepositoryLocationArgs = {
  repositoryLocationName: Scalars['String'];
};

export type DagitMutationStartScheduleArgs = {
  scheduleSelector: ScheduleSelector;
};

export type DagitMutationStartSensorArgs = {
  sensorSelector: SensorSelector;
};

export type DagitMutationStopRunningScheduleArgs = {
  scheduleOriginId: Scalars['String'];
  scheduleSelectorId: Scalars['String'];
};

export type DagitMutationStopSensorArgs = {
  jobOriginId: Scalars['String'];
  jobSelectorId: Scalars['String'];
};

export type DagitMutationTerminatePipelineExecutionArgs = {
  runId: Scalars['String'];
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

export type DagitMutationTerminateRunArgs = {
  runId: Scalars['String'];
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

export type DagitMutationWipeAssetsArgs = {
  assetKeys: Array<AssetKeyInput>;
};

export type DagitQuery = {
  __typename: 'DagitQuery';
  assetNodeDefinitionCollisions: Array<AssetNodeDefinitionCollision>;
  assetNodeOrError: AssetNodeOrError;
  assetNodes: Array<AssetNode>;
  assetOrError: AssetOrError;
  assetsLatestInfo: Array<AssetLatestInfo>;
  assetsOrError: AssetsOrError;
  capturedLogs: CapturedLogs;
  capturedLogsMetadata: CapturedLogsMetadata;
  executionPlanOrError: ExecutionPlanOrError;
  graphOrError: GraphOrError;
  instance: Instance;
  instigationStateOrError: InstigationStateOrError;
  isPipelineConfigValid: PipelineConfigValidationResult;
  locationStatusesOrError: WorkspaceLocationStatusEntriesOrError;
  logsForRun: EventConnectionOrError;
  partitionBackfillOrError: PartitionBackfillOrError;
  partitionBackfillsOrError: PartitionBackfillsOrError;
  partitionSetOrError: PartitionSetOrError;
  partitionSetsOrError: PartitionSetsOrError;
  permissions: Array<Permission>;
  pipelineOrError: PipelineOrError;
  pipelineRunOrError: RunOrError;
  pipelineRunTags: Array<PipelineTagAndValues>;
  pipelineRunsOrError: RunsOrError;
  pipelineSnapshotOrError: PipelineSnapshotOrError;
  repositoriesOrError: RepositoriesOrError;
  repositoryOrError: RepositoryOrError;
  runConfigSchemaOrError: RunConfigSchemaOrError;
  runGroupOrError: RunGroupOrError;
  runGroupsOrError: RunGroupsOrError;
  runOrError: RunOrError;
  runsOrError: RunsOrError;
  scheduleOrError: ScheduleOrError;
  scheduler: SchedulerOrError;
  schedulesOrError: SchedulesOrError;
  sensorOrError: SensorOrError;
  sensorsOrError: SensorsOrError;
  shouldShowNux: Scalars['Boolean'];
  unloadableInstigationStatesOrError: InstigationStatesOrError;
  version: Scalars['String'];
  workspaceOrError: WorkspaceOrError;
};

export type DagitQueryAssetNodeDefinitionCollisionsArgs = {
  assetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type DagitQueryAssetNodeOrErrorArgs = {
  assetKey: AssetKeyInput;
};

export type DagitQueryAssetNodesArgs = {
  assetKeys?: InputMaybe<Array<AssetKeyInput>>;
  group?: InputMaybe<AssetGroupSelector>;
  loadMaterializations?: InputMaybe<Scalars['Boolean']>;
  pipeline?: InputMaybe<PipelineSelector>;
};

export type DagitQueryAssetOrErrorArgs = {
  assetKey: AssetKeyInput;
};

export type DagitQueryAssetsLatestInfoArgs = {
  assetKeys: Array<AssetKeyInput>;
};

export type DagitQueryAssetsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  prefix?: InputMaybe<Array<Scalars['String']>>;
};

export type DagitQueryCapturedLogsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  logKey: Array<Scalars['String']>;
};

export type DagitQueryCapturedLogsMetadataArgs = {
  logKey: Array<Scalars['String']>;
};

export type DagitQueryExecutionPlanOrErrorArgs = {
  mode: Scalars['String'];
  pipeline: PipelineSelector;
  runConfigData?: InputMaybe<Scalars['RunConfigData']>;
};

export type DagitQueryGraphOrErrorArgs = {
  selector?: InputMaybe<GraphSelector>;
};

export type DagitQueryInstigationStateOrErrorArgs = {
  instigationSelector: InstigationSelector;
};

export type DagitQueryIsPipelineConfigValidArgs = {
  mode: Scalars['String'];
  pipeline: PipelineSelector;
  runConfigData?: InputMaybe<Scalars['RunConfigData']>;
};

export type DagitQueryLogsForRunArgs = {
  afterCursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  runId: Scalars['ID'];
};

export type DagitQueryPartitionBackfillOrErrorArgs = {
  backfillId: Scalars['String'];
};

export type DagitQueryPartitionBackfillsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  status?: InputMaybe<BulkActionStatus>;
};

export type DagitQueryPartitionSetOrErrorArgs = {
  partitionSetName?: InputMaybe<Scalars['String']>;
  repositorySelector: RepositorySelector;
};

export type DagitQueryPartitionSetsOrErrorArgs = {
  pipelineName: Scalars['String'];
  repositorySelector: RepositorySelector;
};

export type DagitQueryPipelineOrErrorArgs = {
  params: PipelineSelector;
};

export type DagitQueryPipelineRunOrErrorArgs = {
  runId: Scalars['ID'];
};

export type DagitQueryPipelineRunsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type DagitQueryPipelineSnapshotOrErrorArgs = {
  activePipelineSelector?: InputMaybe<PipelineSelector>;
  snapshotId?: InputMaybe<Scalars['String']>;
};

export type DagitQueryRepositoriesOrErrorArgs = {
  repositorySelector?: InputMaybe<RepositorySelector>;
};

export type DagitQueryRepositoryOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type DagitQueryRunConfigSchemaOrErrorArgs = {
  mode?: InputMaybe<Scalars['String']>;
  selector: PipelineSelector;
};

export type DagitQueryRunGroupOrErrorArgs = {
  runId: Scalars['ID'];
};

export type DagitQueryRunGroupsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type DagitQueryRunOrErrorArgs = {
  runId: Scalars['ID'];
};

export type DagitQueryRunsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type DagitQueryScheduleOrErrorArgs = {
  scheduleSelector: ScheduleSelector;
};

export type DagitQuerySchedulesOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type DagitQuerySensorOrErrorArgs = {
  sensorSelector: SensorSelector;
};

export type DagitQuerySensorsOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type DagitQueryUnloadableInstigationStatesOrErrorArgs = {
  instigationType?: InputMaybe<InstigationType>;
};

export type DagitSubscription = {
  __typename: 'DagitSubscription';
  capturedLogs: CapturedLogs;
  computeLogs: ComputeLogFile;
  locationStateChangeEvents: LocationStateChangeSubscription;
  pipelineRunLogs: PipelineRunLogsSubscriptionPayload;
};

export type DagitSubscriptionCapturedLogsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  logKey: Array<Scalars['String']>;
};

export type DagitSubscriptionComputeLogsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  ioType: ComputeIoType;
  runId: Scalars['ID'];
  stepKey: Scalars['String'];
};

export type DagitSubscriptionPipelineRunLogsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  runId: Scalars['ID'];
};

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

export type DagsterRunEvent =
  | AlertFailureEvent
  | AlertStartEvent
  | AlertSuccessEvent
  | AssetMaterializationPlannedEvent
  | EngineEvent
  | ExecutionStepFailureEvent
  | ExecutionStepInputEvent
  | ExecutionStepOutputEvent
  | ExecutionStepRestartEvent
  | ExecutionStepSkippedEvent
  | ExecutionStepStartEvent
  | ExecutionStepSuccessEvent
  | ExecutionStepUpForRetryEvent
  | HandledOutputEvent
  | HookCompletedEvent
  | HookErroredEvent
  | HookSkippedEvent
  | LoadedInputEvent
  | LogMessageEvent
  | LogsCapturedEvent
  | MaterializationEvent
  | ObjectStoreOperationEvent
  | ObservationEvent
  | ResourceInitFailureEvent
  | ResourceInitStartedEvent
  | ResourceInitSuccessEvent
  | RunCanceledEvent
  | RunCancelingEvent
  | RunDequeuedEvent
  | RunEnqueuedEvent
  | RunFailureEvent
  | RunStartEvent
  | RunStartingEvent
  | RunSuccessEvent
  | StepExpectationResultEvent
  | StepWorkerStartedEvent
  | StepWorkerStartingEvent;

export type DagsterType = {
  description: Maybe<Scalars['String']>;
  displayName: Scalars['String'];
  innerTypes: Array<DagsterType>;
  inputSchemaType: Maybe<ConfigType>;
  isBuiltin: Scalars['Boolean'];
  isList: Scalars['Boolean'];
  isNothing: Scalars['Boolean'];
  isNullable: Scalars['Boolean'];
  key: Scalars['String'];
  metadataEntries: Array<MetadataEntry>;
  name: Maybe<Scalars['String']>;
  outputSchemaType: Maybe<ConfigType>;
};

export type DagsterTypeNotFoundError = Error & {
  __typename: 'DagsterTypeNotFoundError';
  dagsterTypeName: Scalars['String'];
  message: Scalars['String'];
};

export type DagsterTypeOrError =
  | DagsterTypeNotFoundError
  | PipelineNotFoundError
  | PythonError
  | RegularDagsterType;

export type DefaultPartitions = {
  __typename: 'DefaultPartitions';
  materializedPartitions: Array<Scalars['String']>;
  unmaterializedPartitions: Array<Scalars['String']>;
};

export type DeletePipelineRunResult =
  | DeletePipelineRunSuccess
  | PythonError
  | RunNotFoundError
  | UnauthorizedError;

export type DeletePipelineRunSuccess = {
  __typename: 'DeletePipelineRunSuccess';
  runId: Scalars['String'];
};

export type DeleteRunMutation = {
  __typename: 'DeleteRunMutation';
  Output: DeletePipelineRunResult;
};

export type DimensionDefinitionType = {
  __typename: 'DimensionDefinitionType';
  description: Scalars['String'];
  isPrimaryDimension: Scalars['Boolean'];
  name: Scalars['String'];
  type: PartitionDefinitionType;
};

export type DimensionPartitionKeys = {
  __typename: 'DimensionPartitionKeys';
  name: Scalars['String'];
  partitionKeys: Array<Scalars['String']>;
};

export type DisplayableEvent = {
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
};

export type DryRunInstigationTick = {
  __typename: 'DryRunInstigationTick';
  evaluationResult: Maybe<TickEvaluation>;
  timestamp: Maybe<Scalars['Float']>;
};

export type DryRunInstigationTicks = {
  __typename: 'DryRunInstigationTicks';
  cursor: Scalars['Float'];
  results: Array<DryRunInstigationTick>;
};

export type EngineEvent = DisplayableEvent &
  ErrorEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'EngineEvent';
    description: Maybe<Scalars['String']>;
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type EnumConfigType = ConfigType & {
  __typename: 'EnumConfigType';
  description: Maybe<Scalars['String']>;
  givenName: Scalars['String'];
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
  values: Array<EnumConfigValue>;
};

export type EnumConfigValue = {
  __typename: 'EnumConfigValue';
  description: Maybe<Scalars['String']>;
  value: Scalars['String'];
};

export type Error = {
  message: Scalars['String'];
};

export type ErrorChainLink = Error & {
  __typename: 'ErrorChainLink';
  error: PythonError;
  isExplicitLink: Scalars['Boolean'];
  message: Scalars['String'];
};

export type ErrorEvent = {
  error: Maybe<PythonError>;
};

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

export type EvaluationStack = {
  __typename: 'EvaluationStack';
  entries: Array<EvaluationStackEntry>;
};

export type EvaluationStackEntry =
  | EvaluationStackListItemEntry
  | EvaluationStackMapKeyEntry
  | EvaluationStackMapValueEntry
  | EvaluationStackPathEntry;

export type EvaluationStackListItemEntry = {
  __typename: 'EvaluationStackListItemEntry';
  listIndex: Scalars['Int'];
};

export type EvaluationStackMapKeyEntry = {
  __typename: 'EvaluationStackMapKeyEntry';
  mapKey: Scalars['GenericScalar'];
};

export type EvaluationStackMapValueEntry = {
  __typename: 'EvaluationStackMapValueEntry';
  mapKey: Scalars['GenericScalar'];
};

export type EvaluationStackPathEntry = {
  __typename: 'EvaluationStackPathEntry';
  fieldName: Scalars['String'];
};

export type EventConnection = {
  __typename: 'EventConnection';
  cursor: Scalars['String'];
  events: Array<DagsterRunEvent>;
  hasMore: Scalars['Boolean'];
};

export type EventConnectionOrError = EventConnection | PythonError | RunNotFoundError;

export type ExecutionMetadata = {
  parentRunId?: InputMaybe<Scalars['String']>;
  rootRunId?: InputMaybe<Scalars['String']>;
  runId?: InputMaybe<Scalars['String']>;
  tags?: InputMaybe<Array<ExecutionTag>>;
};

export type ExecutionParams = {
  executionMetadata?: InputMaybe<ExecutionMetadata>;
  mode?: InputMaybe<Scalars['String']>;
  preset?: InputMaybe<Scalars['String']>;
  runConfigData?: InputMaybe<Scalars['RunConfigData']>;
  selector: JobOrPipelineSelector;
  stepKeys?: InputMaybe<Array<Scalars['String']>>;
};

export type ExecutionPlan = {
  __typename: 'ExecutionPlan';
  artifactsPersisted: Scalars['Boolean'];
  steps: Array<ExecutionStep>;
};

export type ExecutionPlanOrError =
  | ExecutionPlan
  | InvalidSubsetError
  | PipelineNotFoundError
  | PythonError
  | RunConfigValidationInvalid;

export type ExecutionStep = {
  __typename: 'ExecutionStep';
  inputs: Array<ExecutionStepInput>;
  key: Scalars['String'];
  kind: StepKind;
  metadata: Array<MetadataItemDefinition>;
  outputs: Array<ExecutionStepOutput>;
  solidHandleID: Scalars['String'];
};

export type ExecutionStepFailureEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepFailureEvent';
    error: Maybe<PythonError>;
    errorSource: Maybe<ErrorSource>;
    eventType: Maybe<DagsterEventType>;
    failureMetadata: Maybe<FailureMetadata>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepInput = {
  __typename: 'ExecutionStepInput';
  dependsOn: Array<ExecutionStep>;
  name: Scalars['String'];
};

export type ExecutionStepInputEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepInputEvent';
    eventType: Maybe<DagsterEventType>;
    inputName: Scalars['String'];
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
    typeCheck: TypeCheck;
  };

export type ExecutionStepOutput = {
  __typename: 'ExecutionStepOutput';
  name: Scalars['String'];
};

export type ExecutionStepOutputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepOutputEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    outputName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
    typeCheck: TypeCheck;
  };

export type ExecutionStepRestartEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepRestartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepSkippedEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepSkippedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepStartEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepStartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepSuccessEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepSuccessEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepUpForRetryEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepUpForRetryEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    secondsToWait: Maybe<Scalars['Int']>;
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionTag = {
  key: Scalars['String'];
  value: Scalars['String'];
};

export type ExpectationResult = DisplayableEvent & {
  __typename: 'ExpectationResult';
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
  success: Scalars['Boolean'];
};

export type FailureMetadata = DisplayableEvent & {
  __typename: 'FailureMetadata';
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
};

export type FieldNotDefinedConfigError = PipelineConfigValidationError & {
  __typename: 'FieldNotDefinedConfigError';
  fieldName: Scalars['String'];
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type FieldsNotDefinedConfigError = PipelineConfigValidationError & {
  __typename: 'FieldsNotDefinedConfigError';
  fieldNames: Array<Scalars['String']>;
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type FloatMetadataEntry = MetadataEntry & {
  __typename: 'FloatMetadataEntry';
  description: Maybe<Scalars['String']>;
  floatValue: Maybe<Scalars['Float']>;
  label: Scalars['String'];
};

export type FreshnessPolicy = {
  __typename: 'FreshnessPolicy';
  cronSchedule: Maybe<Scalars['String']>;
  maximumLagMinutes: Scalars['Float'];
};

export type Graph = SolidContainer & {
  __typename: 'Graph';
  description: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  modes: Array<Mode>;
  name: Scalars['String'];
  solidHandle: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
};

export type GraphSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type GraphSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type GraphNotFoundError = Error & {
  __typename: 'GraphNotFoundError';
  graphName: Scalars['String'];
  message: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type GraphOrError = Graph | GraphNotFoundError | PythonError;

export type GraphSelector = {
  graphName: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type HandledOutputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'HandledOutputEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    managerKey: Scalars['String'];
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    outputName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type HookCompletedEvent = MessageEvent &
  StepEvent & {
    __typename: 'HookCompletedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type HookErroredEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'HookErroredEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type HookSkippedEvent = MessageEvent &
  StepEvent & {
    __typename: 'HookSkippedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type IPipelineSnapshot = {
  dagsterTypeOrError: DagsterTypeOrError;
  dagsterTypes: Array<DagsterType>;
  description: Maybe<Scalars['String']>;
  graphName: Scalars['String'];
  metadataEntries: Array<MetadataEntry>;
  modes: Array<Mode>;
  name: Scalars['String'];
  parentSnapshotId: Maybe<Scalars['String']>;
  pipelineSnapshotId: Scalars['String'];
  runs: Array<Run>;
  schedules: Array<Schedule>;
  sensors: Array<Sensor>;
  solidHandle: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
  tags: Array<PipelineTag>;
};

export type IPipelineSnapshotDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String'];
};

export type IPipelineSnapshotRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type IPipelineSnapshotSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type IPipelineSnapshotSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type ISolidDefinition = {
  assetNodes: Array<AssetNode>;
  description: Maybe<Scalars['String']>;
  inputDefinitions: Array<InputDefinition>;
  metadata: Array<MetadataItemDefinition>;
  name: Scalars['String'];
  outputDefinitions: Array<OutputDefinition>;
};

export type Input = {
  __typename: 'Input';
  definition: InputDefinition;
  dependsOn: Array<Output>;
  isDynamicCollect: Scalars['Boolean'];
  solid: Solid;
};

export type InputDefinition = {
  __typename: 'InputDefinition';
  description: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
  name: Scalars['String'];
  solidDefinition: SolidDefinition;
  type: DagsterType;
};

export type InputMapping = {
  __typename: 'InputMapping';
  definition: InputDefinition;
  mappedInput: Input;
};

export type InputTag = {
  name: Scalars['String'];
  value: Scalars['String'];
};

export type Instance = {
  __typename: 'Instance';
  daemonHealth: DaemonHealth;
  executablePath: Scalars['String'];
  hasCapturedLogManager: Scalars['Boolean'];
  hasInfo: Scalars['Boolean'];
  info: Maybe<Scalars['String']>;
  runLauncher: Maybe<RunLauncher>;
  runQueuingSupported: Scalars['Boolean'];
};

export type InstigationEvent = {
  __typename: 'InstigationEvent';
  level: LogLevel;
  message: Scalars['String'];
  timestamp: Scalars['String'];
};

export type InstigationEventConnection = {
  __typename: 'InstigationEventConnection';
  cursor: Scalars['String'];
  events: Array<InstigationEvent>;
  hasMore: Scalars['Boolean'];
};

export type InstigationSelector = {
  name: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type InstigationState = {
  __typename: 'InstigationState';
  id: Scalars['ID'];
  instigationType: InstigationType;
  name: Scalars['String'];
  nextTick: Maybe<DryRunInstigationTick>;
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  repositoryOrigin: RepositoryOrigin;
  runningCount: Scalars['Int'];
  runs: Array<Run>;
  runsCount: Scalars['Int'];
  selectorId: Scalars['String'];
  status: InstigationStatus;
  tick: Maybe<InstigationTick>;
  ticks: Array<InstigationTick>;
  typeSpecificData: Maybe<InstigationTypeSpecificData>;
};

export type InstigationStateRunsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type InstigationStateTickArgs = {
  timestamp?: InputMaybe<Scalars['Float']>;
};

export type InstigationStateTicksArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  dayOffset?: InputMaybe<Scalars['Int']>;
  dayRange?: InputMaybe<Scalars['Int']>;
  limit?: InputMaybe<Scalars['Int']>;
  statuses?: InputMaybe<Array<InstigationTickStatus>>;
};

export type InstigationStateNotFoundError = Error & {
  __typename: 'InstigationStateNotFoundError';
  message: Scalars['String'];
  name: Scalars['String'];
};

export type InstigationStateOrError =
  | InstigationState
  | InstigationStateNotFoundError
  | PythonError;

export type InstigationStates = {
  __typename: 'InstigationStates';
  results: Array<InstigationState>;
};

export type InstigationStatesOrError = InstigationStates | PythonError;

export enum InstigationStatus {
  RUNNING = 'RUNNING',
  STOPPED = 'STOPPED',
}

export type InstigationTick = {
  __typename: 'InstigationTick';
  cursor: Maybe<Scalars['String']>;
  error: Maybe<PythonError>;
  id: Scalars['ID'];
  logEvents: InstigationEventConnection;
  logKey: Maybe<Array<Scalars['String']>>;
  originRunIds: Array<Scalars['String']>;
  runIds: Array<Scalars['String']>;
  runKeys: Array<Scalars['String']>;
  runs: Array<Run>;
  skipReason: Maybe<Scalars['String']>;
  status: InstigationTickStatus;
  timestamp: Scalars['Float'];
};

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

export type InstigationTypeSpecificData = ScheduleData | SensorData;

export type IntMetadataEntry = MetadataEntry & {
  __typename: 'IntMetadataEntry';
  description: Maybe<Scalars['String']>;
  intRepr: Scalars['String'];
  intValue: Maybe<Scalars['Int']>;
  label: Scalars['String'];
};

export type InvalidOutputError = {
  __typename: 'InvalidOutputError';
  invalidOutputName: Scalars['String'];
  stepKey: Scalars['String'];
};

export type InvalidPipelineRunsFilterError = Error & {
  __typename: 'InvalidPipelineRunsFilterError';
  message: Scalars['String'];
};

export type InvalidStepError = {
  __typename: 'InvalidStepError';
  invalidStepKey: Scalars['String'];
};

export type InvalidSubsetError = Error & {
  __typename: 'InvalidSubsetError';
  message: Scalars['String'];
  pipeline: Pipeline;
};

export type Job = IPipelineSnapshot &
  SolidContainer & {
    __typename: 'Job';
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<DagsterType>;
    description: Maybe<Scalars['String']>;
    graphName: Scalars['String'];
    id: Scalars['ID'];
    isAssetJob: Scalars['Boolean'];
    isJob: Scalars['Boolean'];
    metadataEntries: Array<MetadataEntry>;
    modes: Array<Mode>;
    name: Scalars['String'];
    parentSnapshotId: Maybe<Scalars['String']>;
    pipelineSnapshotId: Scalars['String'];
    presets: Array<PipelinePreset>;
    repository: Repository;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type JobDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String'];
};

export type JobRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type JobSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type JobSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type JobOrPipelineSelector = {
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  jobName?: InputMaybe<Scalars['String']>;
  pipelineName?: InputMaybe<Scalars['String']>;
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  solidSelection?: InputMaybe<Array<Scalars['String']>>;
};

export type JsonMetadataEntry = MetadataEntry & {
  __typename: 'JsonMetadataEntry';
  description: Maybe<Scalars['String']>;
  jsonString: Scalars['String'];
  label: Scalars['String'];
};

export type LaunchBackfillMutation = {
  __typename: 'LaunchBackfillMutation';
  Output: LaunchBackfillResult;
};

export type LaunchBackfillParams = {
  allPartitions?: InputMaybe<Scalars['Boolean']>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  forceSynchronousSubmission?: InputMaybe<Scalars['Boolean']>;
  fromFailure?: InputMaybe<Scalars['Boolean']>;
  partitionNames?: InputMaybe<Array<Scalars['String']>>;
  reexecutionSteps?: InputMaybe<Array<Scalars['String']>>;
  selector?: InputMaybe<PartitionSetSelector>;
  tags?: InputMaybe<Array<ExecutionTag>>;
};

export type LaunchBackfillResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchBackfillSuccess
  | NoModeProvidedError
  | PartitionSetNotFoundError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchBackfillSuccess = {
  __typename: 'LaunchBackfillSuccess';
  backfillId: Scalars['String'];
  launchedRunIds: Maybe<Array<Maybe<Scalars['String']>>>;
};

export type LaunchPipelineRunSuccess = {
  run: Run;
};

export type LaunchRunMutation = {
  __typename: 'LaunchRunMutation';
  Output: LaunchRunResult;
};

export type LaunchRunReexecutionMutation = {
  __typename: 'LaunchRunReexecutionMutation';
  Output: LaunchRunReexecutionResult;
};

export type LaunchRunReexecutionResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchRunSuccess
  | NoModeProvidedError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchRunResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchRunSuccess
  | NoModeProvidedError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchRunSuccess = LaunchPipelineRunSuccess & {
  __typename: 'LaunchRunSuccess';
  run: Run;
};

export type ListDagsterType = DagsterType &
  WrappingDagsterType & {
    __typename: 'ListDagsterType';
    description: Maybe<Scalars['String']>;
    displayName: Scalars['String'];
    innerTypes: Array<DagsterType>;
    inputSchemaType: Maybe<ConfigType>;
    isBuiltin: Scalars['Boolean'];
    isList: Scalars['Boolean'];
    isNothing: Scalars['Boolean'];
    isNullable: Scalars['Boolean'];
    key: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    name: Maybe<Scalars['String']>;
    ofType: DagsterType;
    outputSchemaType: Maybe<ConfigType>;
  };

export type LoadedInputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'LoadedInputEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    inputName: Scalars['String'];
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    managerKey: Scalars['String'];
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
    upstreamOutputName: Maybe<Scalars['String']>;
    upstreamStepKey: Maybe<Scalars['String']>;
  };

export type LocationStateChangeEvent = {
  __typename: 'LocationStateChangeEvent';
  eventType: LocationStateChangeEventType;
  locationName: Scalars['String'];
  message: Scalars['String'];
  serverId: Maybe<Scalars['String']>;
};

export enum LocationStateChangeEventType {
  LOCATION_DISCONNECTED = 'LOCATION_DISCONNECTED',
  LOCATION_ERROR = 'LOCATION_ERROR',
  LOCATION_RECONNECTED = 'LOCATION_RECONNECTED',
  LOCATION_UPDATED = 'LOCATION_UPDATED',
}

export type LocationStateChangeSubscription = {
  __typename: 'LocationStateChangeSubscription';
  event: LocationStateChangeEvent;
};

export enum LogLevel {
  CRITICAL = 'CRITICAL',
  DEBUG = 'DEBUG',
  ERROR = 'ERROR',
  INFO = 'INFO',
  WARNING = 'WARNING',
}

export type LogMessageEvent = MessageEvent & {
  __typename: 'LogMessageEvent';
  eventType: Maybe<DagsterEventType>;
  level: LogLevel;
  message: Scalars['String'];
  runId: Scalars['String'];
  solidHandleID: Maybe<Scalars['String']>;
  stepKey: Maybe<Scalars['String']>;
  timestamp: Scalars['String'];
};

export type LogTelemetryMutationResult = LogTelemetrySuccess | PythonError;

export type LogTelemetrySuccess = {
  __typename: 'LogTelemetrySuccess';
  action: Scalars['String'];
};

export type Logger = {
  __typename: 'Logger';
  configField: Maybe<ConfigTypeField>;
  description: Maybe<Scalars['String']>;
  name: Scalars['String'];
};

export type LogsCapturedEvent = MessageEvent & {
  __typename: 'LogsCapturedEvent';
  eventType: Maybe<DagsterEventType>;
  externalUrl: Maybe<Scalars['String']>;
  fileKey: Scalars['String'];
  level: LogLevel;
  logKey: Scalars['String'];
  message: Scalars['String'];
  pid: Maybe<Scalars['Int']>;
  runId: Scalars['String'];
  solidHandleID: Maybe<Scalars['String']>;
  stepKey: Maybe<Scalars['String']>;
  stepKeys: Maybe<Array<Scalars['String']>>;
  timestamp: Scalars['String'];
};

export type MapConfigType = ConfigType & {
  __typename: 'MapConfigType';
  description: Maybe<Scalars['String']>;
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  keyLabelName: Maybe<Scalars['String']>;
  keyType: ConfigType;
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
  valueType: ConfigType;
};

export type MarkdownMetadataEntry = MetadataEntry & {
  __typename: 'MarkdownMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  mdStr: Scalars['String'];
};

export type MarkerEvent = {
  markerEnd: Maybe<Scalars['String']>;
  markerStart: Maybe<Scalars['String']>;
};

export type MarshalledInput = {
  inputName: Scalars['String'];
  key: Scalars['String'];
};

export type MarshalledOutput = {
  key: Scalars['String'];
  outputName: Scalars['String'];
};

export type MaterializationEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'MaterializationEvent';
    assetKey: Maybe<AssetKey>;
    assetLineage: Array<AssetLineageInfo>;
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    partition: Maybe<Scalars['String']>;
    runId: Scalars['String'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    stepStats: RunStepStats;
    timestamp: Scalars['String'];
  };

export type MaterializationUpstreamDataVersion = {
  __typename: 'MaterializationUpstreamDataVersion';
  assetKey: AssetKey;
  downstreamAssetKey: AssetKey;
  timestamp: Scalars['String'];
};

export type MaterializedPartitionRange2D = {
  __typename: 'MaterializedPartitionRange2D';
  primaryDimEndKey: Scalars['String'];
  primaryDimEndTime: Maybe<Scalars['Float']>;
  primaryDimStartKey: Scalars['String'];
  primaryDimStartTime: Maybe<Scalars['Float']>;
  secondaryDim: PartitionStatus1D;
};

export type MaterializedPartitions = DefaultPartitions | MultiPartitions | TimePartitions;

export type MessageEvent = {
  eventType: Maybe<DagsterEventType>;
  level: LogLevel;
  message: Scalars['String'];
  runId: Scalars['String'];
  solidHandleID: Maybe<Scalars['String']>;
  stepKey: Maybe<Scalars['String']>;
  timestamp: Scalars['String'];
};

export type MetadataEntry = {
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
};

export type MetadataItemDefinition = {
  __typename: 'MetadataItemDefinition';
  key: Scalars['String'];
  value: Scalars['String'];
};

export type MissingFieldConfigError = PipelineConfigValidationError & {
  __typename: 'MissingFieldConfigError';
  field: ConfigTypeField;
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type MissingFieldsConfigError = PipelineConfigValidationError & {
  __typename: 'MissingFieldsConfigError';
  fields: Array<ConfigTypeField>;
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type MissingRunIdErrorEvent = {
  __typename: 'MissingRunIdErrorEvent';
  invalidRunId: Scalars['String'];
};

export type Mode = {
  __typename: 'Mode';
  description: Maybe<Scalars['String']>;
  id: Scalars['String'];
  loggers: Array<Logger>;
  name: Scalars['String'];
  resources: Array<Resource>;
};

export type ModeNotFoundError = Error & {
  __typename: 'ModeNotFoundError';
  message: Scalars['String'];
  mode: Scalars['String'];
};

export type MultiPartitions = {
  __typename: 'MultiPartitions';
  primaryDimensionName: Scalars['String'];
  ranges: Array<MaterializedPartitionRange2D>;
};

export type NoModeProvidedError = Error & {
  __typename: 'NoModeProvidedError';
  message: Scalars['String'];
  pipelineName: Scalars['String'];
};

export type NodeInvocationSite = {
  __typename: 'NodeInvocationSite';
  pipeline: Pipeline;
  solidHandle: SolidHandle;
};

export type NotebookMetadataEntry = MetadataEntry & {
  __typename: 'NotebookMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  path: Scalars['String'];
};

export type NullMetadataEntry = MetadataEntry & {
  __typename: 'NullMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
};

export type NullableConfigType = ConfigType &
  WrappingConfigType & {
    __typename: 'NullableConfigType';
    description: Maybe<Scalars['String']>;
    isSelector: Scalars['Boolean'];
    key: Scalars['String'];
    ofType: ConfigType;
    recursiveConfigTypes: Array<ConfigType>;
    typeParamKeys: Array<Scalars['String']>;
  };

export type NullableDagsterType = DagsterType &
  WrappingDagsterType & {
    __typename: 'NullableDagsterType';
    description: Maybe<Scalars['String']>;
    displayName: Scalars['String'];
    innerTypes: Array<DagsterType>;
    inputSchemaType: Maybe<ConfigType>;
    isBuiltin: Scalars['Boolean'];
    isList: Scalars['Boolean'];
    isNothing: Scalars['Boolean'];
    isNullable: Scalars['Boolean'];
    key: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    name: Maybe<Scalars['String']>;
    ofType: DagsterType;
    outputSchemaType: Maybe<ConfigType>;
  };

export type ObjectStoreOperationEvent = MessageEvent &
  StepEvent & {
    __typename: 'ObjectStoreOperationEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    operationResult: ObjectStoreOperationResult;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ObjectStoreOperationResult = DisplayableEvent & {
  __typename: 'ObjectStoreOperationResult';
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
  op: ObjectStoreOperationType;
};

export enum ObjectStoreOperationType {
  CP_OBJECT = 'CP_OBJECT',
  GET_OBJECT = 'GET_OBJECT',
  RM_OBJECT = 'RM_OBJECT',
  SET_OBJECT = 'SET_OBJECT',
}

export type ObservationEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ObservationEvent';
    assetKey: Maybe<AssetKey>;
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    partition: Maybe<Scalars['String']>;
    runId: Scalars['String'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    stepStats: RunStepStats;
    timestamp: Scalars['String'];
  };

export type Output = {
  __typename: 'Output';
  definition: OutputDefinition;
  dependedBy: Array<Input>;
  solid: Solid;
};

export type OutputDefinition = {
  __typename: 'OutputDefinition';
  description: Maybe<Scalars['String']>;
  isDynamic: Maybe<Scalars['Boolean']>;
  metadataEntries: Array<MetadataEntry>;
  name: Scalars['String'];
  solidDefinition: SolidDefinition;
  type: DagsterType;
};

export type OutputMapping = {
  __typename: 'OutputMapping';
  definition: OutputDefinition;
  mappedOutput: Output;
};

export type Partition = {
  __typename: 'Partition';
  mode: Scalars['String'];
  name: Scalars['String'];
  partitionSetName: Scalars['String'];
  runConfigOrError: PartitionRunConfigOrError;
  runs: Array<Run>;
  solidSelection: Maybe<Array<Scalars['String']>>;
  status: Maybe<RunStatus>;
  tagsOrError: PartitionTagsOrError;
};

export type PartitionRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionBackfill = {
  __typename: 'PartitionBackfill';
  assetSelection: Maybe<Array<AssetKey>>;
  backfillId: Scalars['String'];
  error: Maybe<PythonError>;
  fromFailure: Scalars['Boolean'];
  numCancelable: Scalars['Int'];
  numPartitions: Scalars['Int'];
  partitionNames: Array<Scalars['String']>;
  partitionSet: Maybe<PartitionSet>;
  partitionSetName: Maybe<Scalars['String']>;
  partitionStatusCounts: Array<PartitionStatusCounts>;
  partitionStatuses: PartitionStatuses;
  reexecutionSteps: Maybe<Array<Scalars['String']>>;
  runs: Array<Run>;
  status: BulkActionStatus;
  timestamp: Scalars['Float'];
  unfinishedRuns: Array<Run>;
};

export type PartitionBackfillRunsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionBackfillUnfinishedRunsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionBackfillOrError = PartitionBackfill | PythonError;

export type PartitionBackfills = {
  __typename: 'PartitionBackfills';
  results: Array<PartitionBackfill>;
};

export type PartitionBackfillsOrError = PartitionBackfills | PythonError;

export type PartitionDefinition = {
  __typename: 'PartitionDefinition';
  description: Scalars['String'];
  dimensionTypes: Array<DimensionDefinitionType>;
  timeWindowMetadata: Maybe<TimePartitionsDefinitionMetadata>;
  type: PartitionDefinitionType;
};

export enum PartitionDefinitionType {
  MULTIPARTITIONED = 'MULTIPARTITIONED',
  STATIC = 'STATIC',
  TIME_WINDOW = 'TIME_WINDOW',
}

export type PartitionRun = {
  __typename: 'PartitionRun';
  id: Scalars['String'];
  partitionName: Scalars['String'];
  run: Maybe<Run>;
};

export type PartitionRunConfig = {
  __typename: 'PartitionRunConfig';
  yaml: Scalars['String'];
};

export type PartitionRunConfigOrError = PartitionRunConfig | PythonError;

export type PartitionSet = {
  __typename: 'PartitionSet';
  backfills: Array<PartitionBackfill>;
  id: Scalars['ID'];
  mode: Scalars['String'];
  name: Scalars['String'];
  partition: Maybe<Partition>;
  partitionRuns: Array<PartitionRun>;
  partitionStatusesOrError: PartitionStatusesOrError;
  partitionsOrError: PartitionsOrError;
  pipelineName: Scalars['String'];
  repositoryOrigin: RepositoryOrigin;
  solidSelection: Maybe<Array<Scalars['String']>>;
};

export type PartitionSetBackfillsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionSetPartitionArgs = {
  partitionName: Scalars['String'];
};

export type PartitionSetPartitionsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  reverse?: InputMaybe<Scalars['Boolean']>;
};

export type PartitionSetNotFoundError = Error & {
  __typename: 'PartitionSetNotFoundError';
  message: Scalars['String'];
  partitionSetName: Scalars['String'];
};

export type PartitionSetOrError = PartitionSet | PartitionSetNotFoundError | PythonError;

export type PartitionSetSelector = {
  partitionSetName: Scalars['String'];
  repositorySelector: RepositorySelector;
};

export type PartitionSets = {
  __typename: 'PartitionSets';
  results: Array<PartitionSet>;
};

export type PartitionSetsOrError = PartitionSets | PipelineNotFoundError | PythonError;

export type PartitionStats = {
  __typename: 'PartitionStats';
  numMaterialized: Scalars['Int'];
  numPartitions: Scalars['Int'];
};

export type PartitionStatus = {
  __typename: 'PartitionStatus';
  id: Scalars['String'];
  partitionName: Scalars['String'];
  runDuration: Maybe<Scalars['Float']>;
  runId: Maybe<Scalars['String']>;
  runStatus: Maybe<RunStatus>;
};

export type PartitionStatus1D = DefaultPartitions | TimePartitions;

export type PartitionStatusCounts = {
  __typename: 'PartitionStatusCounts';
  count: Scalars['Int'];
  runStatus: RunStatus;
};

export type PartitionStatuses = {
  __typename: 'PartitionStatuses';
  results: Array<PartitionStatus>;
};

export type PartitionStatusesOrError = PartitionStatuses | PythonError;

export type PartitionTags = {
  __typename: 'PartitionTags';
  results: Array<PipelineTag>;
};

export type PartitionTagsOrError = PartitionTags | PythonError;

export type Partitions = {
  __typename: 'Partitions';
  results: Array<Partition>;
};

export type PartitionsOrError = Partitions | PythonError;

export type PathMetadataEntry = MetadataEntry & {
  __typename: 'PathMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  path: Scalars['String'];
};

export type Permission = {
  __typename: 'Permission';
  disabledReason: Maybe<Scalars['String']>;
  permission: Scalars['String'];
  value: Scalars['Boolean'];
};

export type Pipeline = IPipelineSnapshot &
  SolidContainer & {
    __typename: 'Pipeline';
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<DagsterType>;
    description: Maybe<Scalars['String']>;
    graphName: Scalars['String'];
    id: Scalars['ID'];
    isAssetJob: Scalars['Boolean'];
    isJob: Scalars['Boolean'];
    metadataEntries: Array<MetadataEntry>;
    modes: Array<Mode>;
    name: Scalars['String'];
    parentSnapshotId: Maybe<Scalars['String']>;
    pipelineSnapshotId: Scalars['String'];
    presets: Array<PipelinePreset>;
    repository: Repository;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type PipelineDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String'];
};

export type PipelineRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type PipelineSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type PipelineSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type PipelineConfigValidationError = {
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type PipelineConfigValidationInvalid = {
  errors: Array<PipelineConfigValidationError>;
  pipelineName: Scalars['String'];
};

export type PipelineConfigValidationResult =
  | InvalidSubsetError
  | PipelineConfigValidationValid
  | PipelineNotFoundError
  | PythonError
  | RunConfigValidationInvalid;

export type PipelineConfigValidationValid = {
  __typename: 'PipelineConfigValidationValid';
  pipelineName: Scalars['String'];
};

export type PipelineNotFoundError = Error & {
  __typename: 'PipelineNotFoundError';
  message: Scalars['String'];
  pipelineName: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type PipelineOrError = InvalidSubsetError | Pipeline | PipelineNotFoundError | PythonError;

export type PipelinePreset = {
  __typename: 'PipelinePreset';
  mode: Scalars['String'];
  name: Scalars['String'];
  runConfigYaml: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
  tags: Array<PipelineTag>;
};

export type PipelineReference = {
  name: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
};

export type PipelineRun = {
  assets: Array<Asset>;
  canTerminate: Scalars['Boolean'];
  capturedLogs: CapturedLogs;
  computeLogs: ComputeLogs;
  eventConnection: EventConnection;
  executionPlan: Maybe<ExecutionPlan>;
  id: Scalars['ID'];
  jobName: Scalars['String'];
  mode: Scalars['String'];
  parentRunId: Maybe<Scalars['String']>;
  pipeline: PipelineReference;
  pipelineName: Scalars['String'];
  pipelineSnapshotId: Maybe<Scalars['String']>;
  repositoryOrigin: Maybe<RepositoryOrigin>;
  rootRunId: Maybe<Scalars['String']>;
  runConfig: Scalars['RunConfigData'];
  runConfigYaml: Scalars['String'];
  runId: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
  stats: RunStatsSnapshotOrError;
  status: RunStatus;
  stepKeysToExecute: Maybe<Array<Scalars['String']>>;
  stepStats: Array<RunStepStats>;
  tags: Array<PipelineTag>;
};

export type PipelineRunCapturedLogsArgs = {
  fileKey: Scalars['String'];
};

export type PipelineRunComputeLogsArgs = {
  stepKey: Scalars['String'];
};

export type PipelineRunEventConnectionArgs = {
  afterCursor?: InputMaybe<Scalars['String']>;
};

export type PipelineRunConflict = {
  message: Scalars['String'];
};

export type PipelineRunLogsSubscriptionFailure = {
  __typename: 'PipelineRunLogsSubscriptionFailure';
  message: Scalars['String'];
  missingRunId: Maybe<Scalars['String']>;
};

export type PipelineRunLogsSubscriptionPayload =
  | PipelineRunLogsSubscriptionFailure
  | PipelineRunLogsSubscriptionSuccess;

export type PipelineRunLogsSubscriptionSuccess = {
  __typename: 'PipelineRunLogsSubscriptionSuccess';
  cursor: Scalars['String'];
  hasMorePastEvents: Scalars['Boolean'];
  messages: Array<DagsterRunEvent>;
  run: Run;
};

export type PipelineRunMetadataEntry = MetadataEntry & {
  __typename: 'PipelineRunMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  runId: Scalars['String'];
};

export type PipelineRunNotFoundError = {
  message: Scalars['String'];
  runId: Scalars['String'];
};

export type PipelineRunStatsSnapshot = {
  endTime: Maybe<Scalars['Float']>;
  enqueuedTime: Maybe<Scalars['Float']>;
  expectations: Scalars['Int'];
  id: Scalars['String'];
  launchTime: Maybe<Scalars['Float']>;
  materializations: Scalars['Int'];
  runId: Scalars['String'];
  startTime: Maybe<Scalars['Float']>;
  stepsFailed: Scalars['Int'];
  stepsSucceeded: Scalars['Int'];
};

export type PipelineRunStepStats = {
  endTime: Maybe<Scalars['Float']>;
  expectationResults: Array<ExpectationResult>;
  materializations: Array<MaterializationEvent>;
  runId: Scalars['String'];
  startTime: Maybe<Scalars['Float']>;
  status: Maybe<StepEventStatus>;
  stepKey: Scalars['String'];
};

export type PipelineRuns = {
  count: Maybe<Scalars['Int']>;
  results: Array<Run>;
};

export type PipelineSelector = {
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  pipelineName: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  solidSelection?: InputMaybe<Array<Scalars['String']>>;
};

export type PipelineSnapshot = IPipelineSnapshot &
  PipelineReference &
  SolidContainer & {
    __typename: 'PipelineSnapshot';
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<DagsterType>;
    description: Maybe<Scalars['String']>;
    graphName: Scalars['String'];
    id: Scalars['ID'];
    metadataEntries: Array<MetadataEntry>;
    modes: Array<Mode>;
    name: Scalars['String'];
    parentSnapshotId: Maybe<Scalars['String']>;
    pipelineSnapshotId: Scalars['String'];
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solidSelection: Maybe<Array<Scalars['String']>>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type PipelineSnapshotDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String'];
};

export type PipelineSnapshotRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type PipelineSnapshotSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type PipelineSnapshotSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type PipelineSnapshotNotFoundError = Error & {
  __typename: 'PipelineSnapshotNotFoundError';
  message: Scalars['String'];
  snapshotId: Scalars['String'];
};

export type PipelineSnapshotOrError =
  | PipelineNotFoundError
  | PipelineSnapshot
  | PipelineSnapshotNotFoundError
  | PythonError;

export type PipelineTag = {
  __typename: 'PipelineTag';
  key: Scalars['String'];
  value: Scalars['String'];
};

export type PipelineTagAndValues = {
  __typename: 'PipelineTagAndValues';
  key: Scalars['String'];
  values: Array<Scalars['String']>;
};

export type PresetNotFoundError = Error & {
  __typename: 'PresetNotFoundError';
  message: Scalars['String'];
  preset: Scalars['String'];
};

export type PythonArtifactMetadataEntry = MetadataEntry & {
  __typename: 'PythonArtifactMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  module: Scalars['String'];
  name: Scalars['String'];
};

export type PythonError = Error & {
  __typename: 'PythonError';
  cause: Maybe<PythonError>;
  causes: Array<PythonError>;
  className: Maybe<Scalars['String']>;
  errorChain: Array<ErrorChainLink>;
  message: Scalars['String'];
  stack: Array<Scalars['String']>;
};

export type ReexecutionParams = {
  parentRunId: Scalars['String'];
  strategy: ReexecutionStrategy;
};

export enum ReexecutionStrategy {
  ALL_STEPS = 'ALL_STEPS',
  FROM_FAILURE = 'FROM_FAILURE',
}

export type RegularConfigType = ConfigType & {
  __typename: 'RegularConfigType';
  description: Maybe<Scalars['String']>;
  givenName: Scalars['String'];
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
};

export type RegularDagsterType = DagsterType & {
  __typename: 'RegularDagsterType';
  description: Maybe<Scalars['String']>;
  displayName: Scalars['String'];
  innerTypes: Array<DagsterType>;
  inputSchemaType: Maybe<ConfigType>;
  isBuiltin: Scalars['Boolean'];
  isList: Scalars['Boolean'];
  isNothing: Scalars['Boolean'];
  isNullable: Scalars['Boolean'];
  key: Scalars['String'];
  metadataEntries: Array<MetadataEntry>;
  name: Maybe<Scalars['String']>;
  outputSchemaType: Maybe<ConfigType>;
};

export type ReloadNotSupported = Error & {
  __typename: 'ReloadNotSupported';
  message: Scalars['String'];
};

export type ReloadRepositoryLocationMutation = {
  __typename: 'ReloadRepositoryLocationMutation';
  Output: ReloadRepositoryLocationMutationResult;
};

export type ReloadRepositoryLocationMutationResult =
  | PythonError
  | ReloadNotSupported
  | RepositoryLocationNotFound
  | UnauthorizedError
  | WorkspaceLocationEntry;

export type ReloadWorkspaceMutation = {
  __typename: 'ReloadWorkspaceMutation';
  Output: ReloadWorkspaceMutationResult;
};

export type ReloadWorkspaceMutationResult = PythonError | UnauthorizedError | Workspace;

export type RepositoriesOrError = PythonError | RepositoryConnection;

export type Repository = {
  __typename: 'Repository';
  assetGroups: Array<AssetGroup>;
  assetNodes: Array<AssetNode>;
  displayMetadata: Array<RepositoryMetadata>;
  id: Scalars['ID'];
  jobs: Array<Job>;
  location: RepositoryLocation;
  name: Scalars['String'];
  origin: RepositoryOrigin;
  partitionSets: Array<PartitionSet>;
  pipelines: Array<Pipeline>;
  schedules: Array<Schedule>;
  sensors: Array<Sensor>;
  usedSolid: Maybe<UsedSolid>;
  usedSolids: Array<UsedSolid>;
};

export type RepositoryUsedSolidArgs = {
  name: Scalars['String'];
};

export type RepositoryConnection = {
  __typename: 'RepositoryConnection';
  nodes: Array<Repository>;
};

export type RepositoryLocation = {
  __typename: 'RepositoryLocation';
  environmentPath: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  isReloadSupported: Scalars['Boolean'];
  name: Scalars['String'];
  repositories: Array<Repository>;
  serverId: Maybe<Scalars['String']>;
};

export enum RepositoryLocationLoadStatus {
  LOADED = 'LOADED',
  LOADING = 'LOADING',
}

export type RepositoryLocationNotFound = Error & {
  __typename: 'RepositoryLocationNotFound';
  message: Scalars['String'];
};

export type RepositoryLocationOrLoadError = PythonError | RepositoryLocation;

export type RepositoryMetadata = {
  __typename: 'RepositoryMetadata';
  key: Scalars['String'];
  value: Scalars['String'];
};

export type RepositoryNotFoundError = Error & {
  __typename: 'RepositoryNotFoundError';
  message: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type RepositoryOrError = PythonError | Repository | RepositoryNotFoundError;

export type RepositoryOrigin = {
  __typename: 'RepositoryOrigin';
  id: Scalars['String'];
  repositoryLocationMetadata: Array<RepositoryMetadata>;
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type RepositorySelector = {
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type Resource = {
  __typename: 'Resource';
  configField: Maybe<ConfigTypeField>;
  description: Maybe<Scalars['String']>;
  name: Scalars['String'];
};

export type ResourceInitFailureEvent = DisplayableEvent &
  ErrorEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ResourceInitFailureEvent';
    description: Maybe<Scalars['String']>;
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ResourceInitStartedEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ResourceInitStartedEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ResourceInitSuccessEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ResourceInitSuccessEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ResourceRequirement = {
  __typename: 'ResourceRequirement';
  resourceKey: Scalars['String'];
};

export type ResumeBackfillResult = PythonError | ResumeBackfillSuccess | UnauthorizedError;

export type ResumeBackfillSuccess = {
  __typename: 'ResumeBackfillSuccess';
  backfillId: Scalars['String'];
};

export type Run = PipelineRun & {
  __typename: 'Run';
  assetMaterializations: Array<MaterializationEvent>;
  assetSelection: Maybe<Array<AssetKey>>;
  assets: Array<Asset>;
  canTerminate: Scalars['Boolean'];
  capturedLogs: CapturedLogs;
  computeLogs: ComputeLogs;
  endTime: Maybe<Scalars['Float']>;
  eventConnection: EventConnection;
  executionPlan: Maybe<ExecutionPlan>;
  id: Scalars['ID'];
  jobName: Scalars['String'];
  mode: Scalars['String'];
  parentPipelineSnapshotId: Maybe<Scalars['String']>;
  parentRunId: Maybe<Scalars['String']>;
  pipeline: PipelineReference;
  pipelineName: Scalars['String'];
  pipelineSnapshotId: Maybe<Scalars['String']>;
  repositoryOrigin: Maybe<RepositoryOrigin>;
  resolvedOpSelection: Maybe<Array<Scalars['String']>>;
  rootRunId: Maybe<Scalars['String']>;
  runConfig: Scalars['RunConfigData'];
  runConfigYaml: Scalars['String'];
  runId: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
  startTime: Maybe<Scalars['Float']>;
  stats: RunStatsSnapshotOrError;
  status: RunStatus;
  stepKeysToExecute: Maybe<Array<Scalars['String']>>;
  stepStats: Array<RunStepStats>;
  tags: Array<PipelineTag>;
  updateTime: Maybe<Scalars['Float']>;
};

export type RunCapturedLogsArgs = {
  fileKey: Scalars['String'];
};

export type RunComputeLogsArgs = {
  stepKey: Scalars['String'];
};

export type RunEventConnectionArgs = {
  afterCursor?: InputMaybe<Scalars['String']>;
};

export type RunCanceledEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunCanceledEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunCancelingEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunCancelingEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunConfigSchema = {
  __typename: 'RunConfigSchema';
  allConfigTypes: Array<ConfigType>;
  isRunConfigValid: PipelineConfigValidationResult;
  rootConfigType: ConfigType;
};

export type RunConfigSchemaIsRunConfigValidArgs = {
  runConfigData?: InputMaybe<Scalars['RunConfigData']>;
};

export type RunConfigSchemaOrError =
  | InvalidSubsetError
  | ModeNotFoundError
  | PipelineNotFoundError
  | PythonError
  | RunConfigSchema;

export type RunConfigValidationInvalid = PipelineConfigValidationInvalid & {
  __typename: 'RunConfigValidationInvalid';
  errors: Array<PipelineConfigValidationError>;
  pipelineName: Scalars['String'];
};

export type RunConflict = Error &
  PipelineRunConflict & {
    __typename: 'RunConflict';
    message: Scalars['String'];
  };

export type RunDequeuedEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunDequeuedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunEnqueuedEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunEnqueuedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunEvent = {
  pipelineName: Scalars['String'];
};

export type RunFailureEvent = ErrorEvent &
  MessageEvent &
  RunEvent & {
    __typename: 'RunFailureEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunGroup = {
  __typename: 'RunGroup';
  rootRunId: Scalars['String'];
  runs: Maybe<Array<Maybe<Run>>>;
};

export type RunGroupNotFoundError = Error & {
  __typename: 'RunGroupNotFoundError';
  message: Scalars['String'];
  runId: Scalars['String'];
};

export type RunGroupOrError = PythonError | RunGroup | RunGroupNotFoundError;

export type RunGroups = {
  __typename: 'RunGroups';
  results: Array<RunGroup>;
};

export type RunGroupsOrError = {
  __typename: 'RunGroupsOrError';
  results: Array<RunGroup>;
};

export type RunLauncher = {
  __typename: 'RunLauncher';
  name: Scalars['String'];
};

export type RunMarker = {
  __typename: 'RunMarker';
  endTime: Maybe<Scalars['Float']>;
  startTime: Maybe<Scalars['Float']>;
};

export type RunNotFoundError = Error &
  PipelineRunNotFoundError & {
    __typename: 'RunNotFoundError';
    message: Scalars['String'];
    runId: Scalars['String'];
  };

export type RunOrError = PythonError | Run | RunNotFoundError;

export type RunRequest = {
  __typename: 'RunRequest';
  runConfigYaml: Scalars['String'];
  runKey: Maybe<Scalars['String']>;
  tags: Array<PipelineTag>;
};

export type RunStartEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunStartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunStartingEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunStartingEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunStatsSnapshot = PipelineRunStatsSnapshot & {
  __typename: 'RunStatsSnapshot';
  endTime: Maybe<Scalars['Float']>;
  enqueuedTime: Maybe<Scalars['Float']>;
  expectations: Scalars['Int'];
  id: Scalars['String'];
  launchTime: Maybe<Scalars['Float']>;
  materializations: Scalars['Int'];
  runId: Scalars['String'];
  startTime: Maybe<Scalars['Float']>;
  stepsFailed: Scalars['Int'];
  stepsSucceeded: Scalars['Int'];
};

export type RunStatsSnapshotOrError = PythonError | RunStatsSnapshot;

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

export type RunStepStats = PipelineRunStepStats & {
  __typename: 'RunStepStats';
  attempts: Array<RunMarker>;
  endTime: Maybe<Scalars['Float']>;
  expectationResults: Array<ExpectationResult>;
  markers: Array<RunMarker>;
  materializations: Array<MaterializationEvent>;
  runId: Scalars['String'];
  startTime: Maybe<Scalars['Float']>;
  status: Maybe<StepEventStatus>;
  stepKey: Scalars['String'];
};

export type RunSuccessEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunSuccessEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type Runs = PipelineRuns & {
  __typename: 'Runs';
  count: Maybe<Scalars['Int']>;
  results: Array<Run>;
};

export type RunsFilter = {
  createdBefore?: InputMaybe<Scalars['Float']>;
  mode?: InputMaybe<Scalars['String']>;
  pipelineName?: InputMaybe<Scalars['String']>;
  runIds?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
  snapshotId?: InputMaybe<Scalars['String']>;
  statuses?: InputMaybe<Array<RunStatus>>;
  tags?: InputMaybe<Array<ExecutionTag>>;
  updatedAfter?: InputMaybe<Scalars['Float']>;
};

export type RunsOrError = InvalidPipelineRunsFilterError | PythonError | Runs;

export type RuntimeMismatchConfigError = PipelineConfigValidationError & {
  __typename: 'RuntimeMismatchConfigError';
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
  valueRep: Maybe<Scalars['String']>;
};

export type ScalarUnionConfigType = ConfigType & {
  __typename: 'ScalarUnionConfigType';
  description: Maybe<Scalars['String']>;
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  nonScalarType: ConfigType;
  nonScalarTypeKey: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  scalarType: ConfigType;
  scalarTypeKey: Scalars['String'];
  typeParamKeys: Array<Scalars['String']>;
};

export type Schedule = {
  __typename: 'Schedule';
  cronSchedule: Scalars['String'];
  description: Maybe<Scalars['String']>;
  executionTimezone: Maybe<Scalars['String']>;
  futureTick: DryRunInstigationTick;
  futureTicks: DryRunInstigationTicks;
  id: Scalars['ID'];
  mode: Scalars['String'];
  name: Scalars['String'];
  partitionSet: Maybe<PartitionSet>;
  pipelineName: Scalars['String'];
  scheduleState: InstigationState;
  solidSelection: Maybe<Array<Maybe<Scalars['String']>>>;
};

export type ScheduleFutureTickArgs = {
  tickTimestamp: Scalars['Int'];
};

export type ScheduleFutureTicksArgs = {
  cursor?: InputMaybe<Scalars['Float']>;
  limit?: InputMaybe<Scalars['Int']>;
  until?: InputMaybe<Scalars['Float']>;
};

export type ScheduleData = {
  __typename: 'ScheduleData';
  cronSchedule: Scalars['String'];
  startTimestamp: Maybe<Scalars['Float']>;
};

export type ScheduleMutationResult = PythonError | ScheduleStateResult | UnauthorizedError;

export type ScheduleNotFoundError = Error & {
  __typename: 'ScheduleNotFoundError';
  message: Scalars['String'];
  scheduleName: Scalars['String'];
};

export type ScheduleOrError = PythonError | Schedule | ScheduleNotFoundError;

export type ScheduleSelector = {
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  scheduleName: Scalars['String'];
};

export type ScheduleStateResult = {
  __typename: 'ScheduleStateResult';
  scheduleState: InstigationState;
};

export enum ScheduleStatus {
  ENDED = 'ENDED',
  RUNNING = 'RUNNING',
  STOPPED = 'STOPPED',
}

export type ScheduleTick = {
  __typename: 'ScheduleTick';
  status: InstigationTickStatus;
  tickId: Scalars['String'];
  tickSpecificData: Maybe<ScheduleTickSpecificData>;
  timestamp: Scalars['Float'];
};

export type ScheduleTickFailureData = {
  __typename: 'ScheduleTickFailureData';
  error: PythonError;
};

export type ScheduleTickSpecificData = ScheduleTickFailureData | ScheduleTickSuccessData;

export type ScheduleTickSuccessData = {
  __typename: 'ScheduleTickSuccessData';
  run: Maybe<Run>;
};

export type Scheduler = {
  __typename: 'Scheduler';
  schedulerClass: Maybe<Scalars['String']>;
};

export type SchedulerNotDefinedError = Error & {
  __typename: 'SchedulerNotDefinedError';
  message: Scalars['String'];
};

export type SchedulerOrError = PythonError | Scheduler | SchedulerNotDefinedError;

export type Schedules = {
  __typename: 'Schedules';
  results: Array<Schedule>;
};

export type SchedulesOrError = PythonError | RepositoryNotFoundError | Schedules;

export type SelectorTypeConfigError = PipelineConfigValidationError & {
  __typename: 'SelectorTypeConfigError';
  incomingFields: Array<Scalars['String']>;
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type Sensor = {
  __typename: 'Sensor';
  description: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  jobOriginId: Scalars['String'];
  metadata: SensorMetadata;
  minIntervalSeconds: Scalars['Int'];
  name: Scalars['String'];
  nextTick: Maybe<DryRunInstigationTick>;
  sensorState: InstigationState;
  targets: Maybe<Array<Target>>;
};

export type SensorData = {
  __typename: 'SensorData';
  lastCursor: Maybe<Scalars['String']>;
  lastRunKey: Maybe<Scalars['String']>;
  lastTickTimestamp: Maybe<Scalars['Float']>;
};

export type SensorMetadata = {
  __typename: 'SensorMetadata';
  assetKeys: Maybe<Array<AssetKey>>;
};

export type SensorNotFoundError = Error & {
  __typename: 'SensorNotFoundError';
  message: Scalars['String'];
  sensorName: Scalars['String'];
};

export type SensorOrError = PythonError | Sensor | SensorNotFoundError | UnauthorizedError;

export type SensorSelector = {
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  sensorName: Scalars['String'];
};

export type Sensors = {
  __typename: 'Sensors';
  results: Array<Sensor>;
};

export type SensorsOrError = PythonError | RepositoryNotFoundError | Sensors;

export type SetSensorCursorMutation = {
  __typename: 'SetSensorCursorMutation';
  Output: SensorOrError;
};

export type ShutdownRepositoryLocationMutation = {
  __typename: 'ShutdownRepositoryLocationMutation';
  Output: ShutdownRepositoryLocationMutationResult;
};

export type ShutdownRepositoryLocationMutationResult =
  | PythonError
  | RepositoryLocationNotFound
  | ShutdownRepositoryLocationSuccess
  | UnauthorizedError;

export type ShutdownRepositoryLocationSuccess = {
  __typename: 'ShutdownRepositoryLocationSuccess';
  repositoryLocationName: Scalars['String'];
};

export type Solid = {
  __typename: 'Solid';
  definition: ISolidDefinition;
  inputs: Array<Input>;
  isDynamicMapped: Scalars['Boolean'];
  name: Scalars['String'];
  outputs: Array<Output>;
};

export type SolidContainer = {
  description: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  modes: Array<Mode>;
  name: Scalars['String'];
  solidHandle: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
};

export type SolidContainerSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type SolidContainerSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type SolidDefinition = ISolidDefinition & {
  __typename: 'SolidDefinition';
  assetNodes: Array<AssetNode>;
  configField: Maybe<ConfigTypeField>;
  description: Maybe<Scalars['String']>;
  inputDefinitions: Array<InputDefinition>;
  metadata: Array<MetadataItemDefinition>;
  name: Scalars['String'];
  outputDefinitions: Array<OutputDefinition>;
  requiredResources: Array<ResourceRequirement>;
};

export type SolidHandle = {
  __typename: 'SolidHandle';
  handleID: Scalars['String'];
  parent: Maybe<SolidHandle>;
  solid: Solid;
  stepStats: Maybe<SolidStepStatsOrError>;
};

export type SolidHandleStepStatsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type SolidStepStatsConnection = {
  __typename: 'SolidStepStatsConnection';
  nodes: Array<RunStepStats>;
};

export type SolidStepStatsOrError = SolidStepStatsConnection | SolidStepStatusUnavailableError;

export type SolidStepStatusUnavailableError = Error & {
  __typename: 'SolidStepStatusUnavailableError';
  message: Scalars['String'];
};

export type StartScheduleMutation = {
  __typename: 'StartScheduleMutation';
  Output: ScheduleMutationResult;
};

export type StepEvent = {
  solidHandleID: Maybe<Scalars['String']>;
  stepKey: Maybe<Scalars['String']>;
};

export enum StepEventStatus {
  FAILURE = 'FAILURE',
  IN_PROGRESS = 'IN_PROGRESS',
  SKIPPED = 'SKIPPED',
  SUCCESS = 'SUCCESS',
}

export type StepExecution = {
  marshalledInputs?: InputMaybe<Array<MarshalledInput>>;
  marshalledOutputs?: InputMaybe<Array<MarshalledOutput>>;
  stepKey: Scalars['String'];
};

export type StepExpectationResultEvent = MessageEvent &
  StepEvent & {
    __typename: 'StepExpectationResultEvent';
    eventType: Maybe<DagsterEventType>;
    expectationResult: ExpectationResult;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export enum StepKind {
  COMPUTE = 'COMPUTE',
  UNRESOLVED_COLLECT = 'UNRESOLVED_COLLECT',
  UNRESOLVED_MAPPED = 'UNRESOLVED_MAPPED',
}

export type StepOutputHandle = {
  outputName: Scalars['String'];
  stepKey: Scalars['String'];
};

export type StepWorkerStartedEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'StepWorkerStartedEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type StepWorkerStartingEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'StepWorkerStartingEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type StopRunningScheduleMutation = {
  __typename: 'StopRunningScheduleMutation';
  Output: ScheduleMutationResult;
};

export type StopSensorMutation = {
  __typename: 'StopSensorMutation';
  Output: StopSensorMutationResultOrError;
};

export type StopSensorMutationResult = {
  __typename: 'StopSensorMutationResult';
  instigationState: Maybe<InstigationState>;
};

export type StopSensorMutationResultOrError =
  | PythonError
  | StopSensorMutationResult
  | UnauthorizedError;

export type Table = {
  __typename: 'Table';
  records: Array<Scalars['String']>;
  schema: TableSchema;
};

export type TableColumn = {
  __typename: 'TableColumn';
  constraints: TableColumnConstraints;
  description: Maybe<Scalars['String']>;
  name: Scalars['String'];
  type: Scalars['String'];
};

export type TableColumnConstraints = {
  __typename: 'TableColumnConstraints';
  nullable: Scalars['Boolean'];
  other: Array<Scalars['String']>;
  unique: Scalars['Boolean'];
};

export type TableConstraints = {
  __typename: 'TableConstraints';
  other: Array<Scalars['String']>;
};

export type TableMetadataEntry = MetadataEntry & {
  __typename: 'TableMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  table: Table;
};

export type TableSchema = {
  __typename: 'TableSchema';
  columns: Array<TableColumn>;
  constraints: Maybe<TableConstraints>;
};

export type TableSchemaMetadataEntry = MetadataEntry & {
  __typename: 'TableSchemaMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  schema: TableSchema;
};

export type Target = {
  __typename: 'Target';
  mode: Scalars['String'];
  pipelineName: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
};

export type TerminatePipelineExecutionFailure = {
  message: Scalars['String'];
  run: Run;
};

export type TerminatePipelineExecutionSuccess = {
  run: Run;
};

export type TerminateRunFailure = TerminatePipelineExecutionFailure & {
  __typename: 'TerminateRunFailure';
  message: Scalars['String'];
  run: Run;
};

export type TerminateRunMutation = {
  __typename: 'TerminateRunMutation';
  Output: TerminateRunResult;
};

export enum TerminateRunPolicy {
  MARK_AS_CANCELED_IMMEDIATELY = 'MARK_AS_CANCELED_IMMEDIATELY',
  SAFE_TERMINATE = 'SAFE_TERMINATE',
}

export type TerminateRunResult =
  | PythonError
  | RunNotFoundError
  | TerminateRunFailure
  | TerminateRunSuccess
  | UnauthorizedError;

export type TerminateRunSuccess = TerminatePipelineExecutionSuccess & {
  __typename: 'TerminateRunSuccess';
  run: Run;
};

export type TextMetadataEntry = MetadataEntry & {
  __typename: 'TextMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  text: Scalars['String'];
};

export type TickEvaluation = {
  __typename: 'TickEvaluation';
  cursor: Maybe<Scalars['String']>;
  error: Maybe<PythonError>;
  runRequests: Maybe<Array<Maybe<RunRequest>>>;
  skipReason: Maybe<Scalars['String']>;
};

export type TimePartitionRange = {
  __typename: 'TimePartitionRange';
  endKey: Scalars['String'];
  endTime: Scalars['Float'];
  startKey: Scalars['String'];
  startTime: Scalars['Float'];
};

export type TimePartitions = {
  __typename: 'TimePartitions';
  ranges: Array<TimePartitionRange>;
};

export type TimePartitionsDefinitionMetadata = {
  __typename: 'TimePartitionsDefinitionMetadata';
  endKey: Scalars['String'];
  endTime: Scalars['Float'];
  startKey: Scalars['String'];
  startTime: Scalars['Float'];
};

export type TypeCheck = DisplayableEvent & {
  __typename: 'TypeCheck';
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
  success: Scalars['Boolean'];
};

export type UnauthorizedError = Error & {
  __typename: 'UnauthorizedError';
  message: Scalars['String'];
};

export type UnknownPipeline = PipelineReference & {
  __typename: 'UnknownPipeline';
  name: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
};

export type UrlMetadataEntry = MetadataEntry & {
  __typename: 'UrlMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  url: Scalars['String'];
};

export type UsedSolid = {
  __typename: 'UsedSolid';
  definition: ISolidDefinition;
  invocations: Array<NodeInvocationSite>;
};

export type Workspace = {
  __typename: 'Workspace';
  locationEntries: Array<WorkspaceLocationEntry>;
};

export type WorkspaceLocationEntry = {
  __typename: 'WorkspaceLocationEntry';
  displayMetadata: Array<RepositoryMetadata>;
  id: Scalars['ID'];
  loadStatus: RepositoryLocationLoadStatus;
  locationOrLoadError: Maybe<RepositoryLocationOrLoadError>;
  name: Scalars['String'];
  permissions: Array<Permission>;
  updatedTimestamp: Scalars['Float'];
};

export type WorkspaceLocationStatusEntries = {
  __typename: 'WorkspaceLocationStatusEntries';
  entries: Array<WorkspaceLocationStatusEntry>;
};

export type WorkspaceLocationStatusEntriesOrError = PythonError | WorkspaceLocationStatusEntries;

export type WorkspaceLocationStatusEntry = {
  __typename: 'WorkspaceLocationStatusEntry';
  id: Scalars['ID'];
  loadStatus: RepositoryLocationLoadStatus;
  name: Scalars['String'];
  updateTimestamp: Scalars['Float'];
};

export type WorkspaceOrError = PythonError | Workspace;

export type WrappingConfigType = {
  ofType: ConfigType;
};

export type WrappingDagsterType = {
  ofType: DagsterType;
};
